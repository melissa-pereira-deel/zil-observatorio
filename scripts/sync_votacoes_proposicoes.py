#!/usr/bin/env python3
"""
Sync votações for each proposição via Câmara API.

Fetches votações from GET /proposicoes/{id}/votacoes for all proposições
in the database, then fetches individual votes for each new votação.

Usage:
    python scripts/sync_votacoes_proposicoes.py [OPTIONS]

Options:
    --proposicao-id ID   Sync a single proposição (by UUID)
    --skip-with-votes    Skip proposições that already have votações (default: true)
    --no-skip            Don't skip proposições that already have votações
    --dry-run            Show what would be synced without persisting

See: specs/002-legislative-enrichment-pipeline/contracts/api.md
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add repo root + apps/api to sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from core.config import settings
from models import Proposicao, Votacao, Voto, Parlamentar, FonteEnum, VotoEnum
from packages.camara_client import CamaraClient
from apps.workers.classifiers import classificar_votacao

logger = logging.getLogger(__name__)

# O mapa de tipoVoto é um só para os três syncs da Câmara.
from apps.workers.crawlers.camara import normalizar_voto  # noqa: E402


def sync_votacoes_por_proposicao(
    db: Session,
    proposicao_ids: Optional[list[UUID]] = None,
    skip_existing: bool = True,
    dry_run: bool = False,
) -> dict:
    """Sync votações from Câmara API for each proposição in the database.

    For each proposição (or subset), fetches votações via
    GET /proposicoes/{fonte_id}/votacoes and syncs votações + individual votos.

    Args:
        db: SQLAlchemy session.
        proposicao_ids: Specific proposição UUIDs to sync (default: all CAMARA).
        skip_existing: Skip proposições that already have ≥1 votação linked.
        dry_run: Show what would be synced without persisting.

    Returns:
        Stats dict with counts of operations performed.
    """
    stats = {
        "proposicoes_checadas": 0,
        "com_votacoes": 0,
        "votacoes_novas": 0,
        "votos_novos": 0,
        "erros": 0,
        "puladas_com_votos": 0,
    }

    # Build query for proposições to process
    query = select(Proposicao).where(Proposicao.fonte == FonteEnum.CAMARA)
    if proposicao_ids:
        query = query.where(Proposicao.id.in_(proposicao_ids))

    proposicoes = db.execute(query).scalars().all()
    total = len(proposicoes)

    if total == 0:
        print("Nenhuma proposição encontrada para sincronizar.")
        return stats

    print(f"Sincronizando votações para {total} proposições...")
    if dry_run:
        print("[DRY RUN — nenhuma mudança será gravada]")

    with CamaraClient() as client:
        for i, prop in enumerate(proposicoes):
            stats["proposicoes_checadas"] += 1
            label = f"{prop.tipo} {prop.numero}/{prop.ano}" if prop.tipo else prop.fonte_id

            # Skip if already has votações
            if skip_existing:
                existing_count = db.execute(
                    select(func.count(Votacao.id)).where(
                        Votacao.proposicao_id == prop.id
                    )
                ).scalar()
                if existing_count and existing_count > 0:
                    stats["puladas_com_votos"] += 1
                    continue

            # Fetch votações from API
            try:
                votacoes_api = client.listar_votacoes_proposicao(int(prop.fonte_id))
            except Exception as e:
                logger.warning(f"Erro ao buscar votações para {label}: {e}")
                stats["erros"] += 1
                continue

            if not votacoes_api:
                continue

            stats["com_votacoes"] += 1
            prop_votacoes_novas = 0
            prop_votos_novos = 0

            linked_existing = False

            for vot in votacoes_api:
                # Dedup: check if votação already exists (R2)
                existing_vot = db.execute(
                    select(Votacao).where(
                        Votacao.fonte_id == str(vot.id),
                        Votacao.fonte == FonteEnum.CAMARA,
                    )
                ).scalar_one_or_none()

                if existing_vot:
                    # Link to proposição if not already linked
                    if existing_vot.proposicao_id is None and not dry_run:
                        existing_vot.proposicao_id = prop.id
                        linked_existing = True
                    continue

                if dry_run:
                    prop_votacoes_novas += 1
                    continue

                # Classify votação
                texto_classificacao = vot.descricao or ""
                if prop.ementa:
                    texto_classificacao = f"{texto_classificacao} {prop.ementa}"
                categorias = classificar_votacao(texto_classificacao)

                # Create votação — direcao_esperada and peso are NULL (editorial-only)
                votacao = Votacao(
                    fonte_id=str(vot.id),
                    fonte=FonteEnum.CAMARA,
                    proposicao_id=prop.id,
                    data=datetime.fromisoformat(vot.data) if vot.data else None,
                    descricao=vot.descricao,
                    # `vot.aprovacao is False` nunca era verdade: a API manda
                    # inteiro, e `0 is False` é falso. Toda rejeição virava
                    # nulo. Ver `_como_bool` em packages/camara_client.
                    resultado=(
                        None if vot.aprovacao is None
                        else "aprovado" if vot.aprovacao
                        else "rejeitado"
                    ),
                    categorias_zil=categorias if categorias else None,
                    direcao_esperada=None,  # set only by apply_direcoes.py
                    peso=None,  # set only by apply_direcoes.py (model default is 1.0)
                )
                db.add(votacao)
                db.flush()

                # Fetch individual votes
                try:
                    votos_api = client.obter_votos(str(vot.id))
                except Exception as e:
                    logger.warning(f"Erro ao buscar votos para votação {vot.id}: {e}")
                    stats["erros"] += 1
                    votos_api = []

                # Fetch party orientations
                partido_orientacao: dict[str, str] = {}
                try:
                    orientacoes = client.obter_votacao_orientacoes(str(vot.id))
                    for ori in orientacoes:
                        partido = ori.get("siglaPartido") or ori.get("partido") or ""
                        orientacao = ori.get("orientacao") or ori.get("voto") or ""
                        if partido and orientacao:
                            partido_orientacao[partido.upper()] = orientacao
                except Exception as e:
                    logger.debug(f"Orientações não disponíveis para votação {vot.id}: {e}")

                sim_count = 0
                nao_count = 0
                abstencao_count = 0

                for v in votos_api:
                    # Resolve parlamentar
                    parlamentar = db.execute(
                        select(Parlamentar).where(
                            Parlamentar.fonte_id == str(v.deputado_id),
                            Parlamentar.fonte == FonteEnum.CAMARA,
                        )
                    ).scalar_one_or_none()

                    if not parlamentar:
                        # Stub for unknown deputy (same pattern as sync_votacoes)
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
                        orientacao_partido = partido_orientacao.get(
                            v.deputado_partido.upper()
                        )

                    voto_obj = Voto(
                        votacao_id=votacao.id,
                        parlamentar_id=parlamentar.id,
                        voto=voto_enum,
                        orientacao_partido=orientacao_partido,
                    )
                    db.add(voto_obj)
                    prop_votos_novos += 1

                votacao.votos_sim = sim_count
                votacao.votos_nao = nao_count
                votacao.abstencoes = abstencao_count
                prop_votacoes_novas += 1

            # Commit per proposição to avoid large transactions
            if not dry_run and (prop_votacoes_novas > 0 or linked_existing):
                db.commit()

            stats["votacoes_novas"] += prop_votacoes_novas
            stats["votos_novos"] += prop_votos_novos

            if prop_votacoes_novas > 0:
                print(
                    f"  [{i + 1}/{total}] {label}: "
                    f"{prop_votacoes_novas} votações + {prop_votos_novos} votos"
                    f"{' (dry-run)' if dry_run else ''}"
                )

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Sync votações for each proposição via Câmara API"
    )
    parser.add_argument(
        "--proposicao-id",
        type=str,
        help="Sync a single proposição by UUID",
    )
    parser.add_argument(
        "--skip-with-votes",
        action="store_true",
        default=True,
        help="Skip proposições that already have votações (default: true)",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Don't skip proposições that already have votações",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without persisting",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    skip_existing = args.skip_with_votes and not args.no_skip

    proposicao_ids = None
    if args.proposicao_id:
        proposicao_ids = [UUID(args.proposicao_id)]

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        stats = sync_votacoes_por_proposicao(
            db,
            proposicao_ids=proposicao_ids,
            skip_existing=skip_existing,
            dry_run=args.dry_run,
        )

    print(
        f"\nDone."
        f"\n  Proposições checadas: {stats['proposicoes_checadas']}"
        f"\n  Puladas (já com votos): {stats['puladas_com_votos']}"
        f"\n  Com votações na API: {stats['com_votacoes']}"
        f"\n  Votações novas sincronizadas: {stats['votacoes_novas']}"
        f"\n  Votos individuais sincronizados: {stats['votos_novos']}"
        f"\n  Erros: {stats['erros']}"
    )


if __name__ == "__main__":
    main()
