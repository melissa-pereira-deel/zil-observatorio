#!/usr/bin/env python3
"""
Sync targeted ZIL votações by ID into the database.

Usage:
    python scripts/sync_votacoes_zil.py [--dry-run]

Reads fonte_ids from data/direcoes/*.yml and fetches only those specific
votações from the Câmara API — much faster than a full quarterly sync.

Useful for:
- Initial test with a small set of known ZIL votações
- Refreshing specific votações without a full resync

After running, apply directions and recalculate scores:
    python scripts/apply_direcoes.py
    python -m apps.workers.scoring (or run via Celery task)
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add repo root and apps/api to sys.path
_root = Path(__file__).parent.parent
_api_dir = str(_root / "apps" / "api")
for _p in [str(_root), _api_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.config import settings
from models import (
    Parlamentar, Votacao, Voto, Proposicao, IngestionRun,
    FonteEnum, VotoEnum,
)
from packages.camara_client import CamaraClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# O mapa de tipoVoto é um só para os três syncs da Câmara.
from apps.workers.crawlers.camara import normalizar_voto  # noqa: E402


def load_target_ids(data_dir: Path) -> list[dict]:
    """Load all fonte_ids from direcoes YAML files (camara only)."""
    targets = []
    for yml_file in sorted(data_dir.glob("*.yml")):
        with open(yml_file) as fh:
            data = yaml.safe_load(fh)
        for d in (data.get("direcoes") or []):
            if d.get("fonte") == "camara":
                targets.append({
                    "fonte_id": str(d["fonte_id"]),
                    "categoria_principal": d.get("categoria_principal"),
                    "ano": yml_file.stem,
                })
    return targets


def sync_single_votacao(db: Session, client: CamaraClient, fonte_id: str,
                        categoria_hint: str | None = None, dry_run: bool = False) -> bool:
    """Fetch a single votação by ID and persist it with its individual votes."""

    # Check if already in DB
    existing = db.execute(
        select(Votacao).where(
            Votacao.fonte_id == fonte_id,
            Votacao.fonte == FonteEnum.CAMARA,
        )
    ).scalar_one_or_none()

    if existing:
        # Preencher `resultado` se estiver faltando. Enquanto este script
        # comparava `aprovacao is True` — que é falso para o inteiro 1 que a
        # API manda —, toda votação era gravada sem resultado. Corrigir o bug
        # não conserta o que já está no banco, e rodar o seed de novo não
        # ajudava: este retorno vinha antes. Só preenche o que está nulo;
        # nunca sobrescreve.
        if existing.resultado is None and not dry_run:
            detalhes = client.obter_votacao_detalhes(fonte_id)
            aprov = (detalhes or {}).get("aprovacao")
            if aprov is not None:
                existing.resultado = "aprovado" if aprov else "rejeitado"
                db.commit()
                logger.info(
                    f"  ✓ Votação {fonte_id} já existe — resultado preenchido: "
                    f"{existing.resultado}"
                )
                return False
        logger.info(f"  ✓ Votação {fonte_id} já existe (id={existing.id})")
        return False

    logger.info(f"  → Buscando votação {fonte_id}...")
    detalhes = client.obter_votacao_detalhes(fonte_id)
    if not detalhes or not isinstance(detalhes, dict):
        logger.warning(f"  ✗ Votação {fonte_id}: sem dados retornados")
        return False

    descricao = detalhes.get("descricao") or ""
    data_str = detalhes.get("dataHoraRegistro") or detalhes.get("data")
    aprovacao = detalhes.get("aprovacao")

    # Try to link a proposição
    proposicao_id = None
    prop_raw = detalhes.get("proposicaoPrincipal")
    if not prop_raw:
        afetadas = detalhes.get("proposicoesAfetadas") or []
        if afetadas:
            prop_raw = afetadas[0]

    if prop_raw and not dry_run:
        fonte_prop_id = str(prop_raw.get("id", ""))
        if fonte_prop_id:
            existing_prop = db.execute(
                select(Proposicao).where(
                    Proposicao.fonte_id == fonte_prop_id,
                    Proposicao.fonte == FonteEnum.CAMARA,
                )
            ).scalar_one_or_none()

            if existing_prop:
                proposicao_id = existing_prop.id
            else:
                ementa = prop_raw.get("ementa") or prop_raw.get("titulo") or ""
                p = Proposicao(
                    fonte_id=fonte_prop_id,
                    fonte=FonteEnum.CAMARA,
                    tipo=prop_raw.get("siglaTipo") or prop_raw.get("tipo"),
                    numero=prop_raw.get("numero"),
                    ano=prop_raw.get("ano"),
                    ementa=ementa,
                    categorias_zil=[categoria_hint] if categoria_hint else None,
                    classificacao_automatica=False,
                )
                db.add(p)
                db.flush()
                proposicao_id = p.id

    # Build categorias_zil from the hint (for targeted sync, we know the category)
    categorias_zil = [categoria_hint] if categoria_hint else None

    # Não usar `is True` / `is False`: a API da Câmara manda inteiro 1/0, e
    # `1 is True` é falso. Enquanto este bloco usava identidade, `resultado`
    # ficava sempre nulo e a página pública inferia o resultado do placar —
    # exibindo "Rejeitado" em votação simbólica, que não tem placar nenhum.
    resultado = None
    if aprovacao is not None:
        resultado = "aprovado" if aprovacao else "rejeitado"

    if dry_run:
        logger.info(f"  [DRY RUN] Would create votação {fonte_id}: {descricao[:60]}")
        return True

    votacao = Votacao(
        fonte_id=fonte_id,
        fonte=FonteEnum.CAMARA,
        proposicao_id=proposicao_id,
        data=datetime.fromisoformat(data_str) if data_str else None,
        descricao=descricao,
        resultado=resultado,
        categorias_zil=categorias_zil,
    )
    db.add(votacao)
    db.flush()

    # Fetch party orientations
    partido_orientacao: dict[str, str] = {}
    try:
        orientacoes = client.obter_votacao_orientacoes(fonte_id)
        for ori in orientacoes:
            partido = (ori.get("siglaPartido") or ori.get("partido") or "").upper()
            orientacao = ori.get("orientacao") or ori.get("voto") or ""
            if partido and orientacao:
                partido_orientacao[partido] = orientacao
    except Exception as e:
        logger.debug(f"  Orientações não disponíveis: {e}")

    # Fetch individual votes
    logger.info(f"  → Buscando votos individuais de {fonte_id}...")
    votos_api = client.obter_votos(fonte_id)

    sim_count = nao_count = abstencao_count = 0

    for v in votos_api:
        parlamentar = db.execute(
            select(Parlamentar).where(
                Parlamentar.fonte_id == str(v.deputado_id),
                Parlamentar.fonte == FonteEnum.CAMARA,
            )
        ).scalar_one_or_none()

        if not parlamentar:
            parlamentar = Parlamentar(
                fonte_id=str(v.deputado_id),
                fonte=FonteEnum.CAMARA,
                nome=v.deputado_nome,
                partido=v.deputado_partido,
                uf=v.deputado_uf,
            )
            db.add(parlamentar)
            db.flush()

        voto_enum = normalizar_voto(v.voto)
        if voto_enum == VotoEnum.SIM:
            sim_count += 1
        elif voto_enum == VotoEnum.NAO:
            nao_count += 1
        elif voto_enum == VotoEnum.ABSTENCAO:
            abstencao_count += 1

        orientacao_partido = None
        if v.deputado_partido:
            orientacao_partido = partido_orientacao.get(v.deputado_partido.upper())

        db.add(Voto(
            votacao_id=votacao.id,
            parlamentar_id=parlamentar.id,
            voto=voto_enum,
            orientacao_partido=orientacao_partido,
        ))

    votacao.votos_sim = sim_count
    votacao.votos_nao = nao_count
    votacao.abstencoes = abstencao_count

    logger.info(
        f"  ✓ {fonte_id}: {sim_count} sim / {nao_count} não / "
        f"{abstencao_count} abstenção | total: {len(votos_api)} votos"
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync targeted ZIL votações by ID")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data" / "direcoes"
    targets = load_target_ids(data_dir)

    if not targets:
        print("Nenhuma votação da Câmara encontrada nos YAMLs de direcoes.")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Syncing {len(targets)} votações ZIL...")

    engine = create_engine(settings.DATABASE_URL)

    # Record IngestionRun
    run = None
    with Session(engine) as db:
        if not args.dry_run:
            run = IngestionRun(
                tipo="zil_targeted_sync",
                status="running",
                iniciado_em=datetime.utcnow(),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

        count_new = 0
        errors = []

        with CamaraClient() as client:
            for t in targets:
                fonte_id = t["fonte_id"]
                print(f"\n→ {fonte_id} ({t['categoria_principal']}, {t['ano']})")
                try:
                    with Session(engine) as inner_db:
                        new = sync_single_votacao(
                            inner_db, client, fonte_id,
                            categoria_hint=t["categoria_principal"],
                            dry_run=args.dry_run,
                        )
                        if new and not args.dry_run:
                            inner_db.commit()
                            count_new += 1
                except Exception as e:
                    logger.error(f"  ✗ Erro ao sincronizar {fonte_id}: {e}")
                    errors.append({"fonte_id": fonte_id, "erro": str(e)})

        if run and not args.dry_run:
            with Session(engine) as db2:
                run_reload = db2.get(IngestionRun, run.id)
                if run_reload:
                    run_reload.status = "success" if not errors else "partial"
                    run_reload.registros_criados = count_new
                    run_reload.erros_count = len(errors)
                    run_reload.finalizado_em = datetime.utcnow()
                    if errors:
                        run_reload.erro_detalhes = errors
                    db2.commit()

    print(f"\n{'─'*50}")
    print(f"Novas votações criadas: {count_new}")
    if errors:
        print(f"Erros: {len(errors)}")
        for e in errors:
            print(f"  {e['fonte_id']}: {e['erro']}")
    print("\nPróximos passos:")
    print("  python scripts/apply_direcoes.py")
    print("  python -m apps.workers.scoring")


if __name__ == "__main__":
    main()
