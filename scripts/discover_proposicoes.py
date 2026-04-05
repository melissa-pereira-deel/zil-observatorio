"""Descoberta de proposições relevantes para o ZIL via API da Câmara.

Busca proposições por palavras-chave das 9 categorias ZIL, classifica
localmente, e persiste com dados completos no banco.

Uso:
    python scripts/discover_proposicoes.py [--ano-inicio 2020] [--ano-fim 2026] [--enriquecer]

Flags:
    --ano-inicio N   Ano inicial da busca (default: 2020)
    --ano-fim N      Ano final da busca (default: ano corrente)
    --enriquecer     Marca proposições novas para enriquecimento automático
    --dry-run        Apenas mostra o que seria descoberto, sem persistir
"""

import argparse
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

# Setup paths
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.camara_client import CamaraClient
from apps.workers.classifiers import classificar_proposicao, relevancia_score
from core.config import SessionLocal
from models import Proposicao, FonteEnum

logger = logging.getLogger(__name__)

# Grupos de busca: conjuntos de keywords agrupados para minimizar chamadas à API.
# Cada grupo resulta em 1 chamada paginada. Termos mais específicos rendem menos
# falsos positivos que termos genéricos como "pesquisa" ou "exportação".
SEARCH_GROUPS: list[dict] = [
    {
        "label": "ZIL-FER — Fertilizantes",
        "keywords": ["fertilizante", "potássio", "fosfato", "biofertilizante", "Autazes", "Santa Quitéria"],
    },
    {
        "label": "ZIL-MIN — Minerais Estratégicos",
        "keywords": ["nióbio", "terras raras", "lítio", "mineral estratégico", "mineral crítico"],
    },
    {
        "label": "ZIL-SEM — Semicondutores",
        "keywords": ["semicondutor", "microeletrônica", "Padis", "circuito integrado"],
    },
    {
        "label": "ZIL-ENE — Energia",
        "keywords": ["hidrogênio verde", "pré-sal", "fundo soberano", "transição energética", "biocombustível"],
    },
    {
        "label": "ZIL-DIG — Soberania Digital",
        "keywords": ["soberania digital", "proteção de dados", "satélite brasileiro", "fibra óptica"],
    },
    {
        "label": "ZIL-DEF — Defesa",
        "keywords": ["Embraer", "defesa cibernética", "ativo estratégico", "indústria de defesa"],
    },
    {
        "label": "ZIL-EDU — Capital Humano",
        "keywords": ["formação técnica", "repatriação", "pesquisa e desenvolvimento"],
    },
    {
        "label": "ZIL-AGR — Agro-Indústria",
        "keywords": ["agroindústria", "processamento agrícola", "industrialização rural"],
    },
    {
        "label": "ZIL-COM — Comércio",
        "keywords": ["reciprocidade comercial", "anti-dumping", "acordo bilateral", "Mercosul"],
    },
]

# Tipos relevantes de proposição (filtro na API)
TIPOS_PROPOSICAO = ["PL", "PLP", "PEC", "PDL", "MPV"]


def discover(
    db: Session,
    ano_inicio: int = 2020,
    ano_fim: int | None = None,
    enriquecer: bool = False,
    dry_run: bool = False,
) -> dict:
    """Busca e persiste proposições relevantes para o ZIL.

    Returns:
        Dict com contagens: total_buscadas, novas, ja_existentes, classificadas.
    """
    if ano_fim is None:
        ano_fim = date.today().year

    stats = {
        "total_buscadas": 0,
        "novas": 0,
        "ja_existentes": 0,
        "classificadas_zil": 0,
        "erros": 0,
    }

    # Deduplicar proposições encontradas em múltiplos grupos
    seen_fonte_ids: set[str] = set()

    client = CamaraClient()

    try:
        for group in SEARCH_GROUPS:
            label = group["label"]
            keywords = group["keywords"]

            logger.info(f"\n{'='*60}")
            logger.info(f"Buscando: {label}")
            logger.info(f"  Keywords: {', '.join(keywords)}")
            logger.info(f"  Período: {ano_inicio}–{ano_fim}")

            try:
                resultados = client.pesquisar_proposicoes(
                    keywords=keywords,
                    ano_inicio=ano_inicio,
                    ano_fim=ano_fim,
                    tipos=TIPOS_PROPOSICAO,
                )
            except Exception as e:
                logger.error(f"  Erro na busca: {e}")
                stats["erros"] += 1
                continue

            logger.info(f"  Encontradas: {len(resultados)} proposições")
            stats["total_buscadas"] += len(resultados)

            for prop in resultados:
                fonte_id = str(prop.id)

                # Dedup dentro desta execução
                if fonte_id in seen_fonte_ids:
                    continue
                seen_fonte_ids.add(fonte_id)

                # Já existe no banco?
                existing = db.execute(
                    select(Proposicao).where(
                        Proposicao.fonte_id == fonte_id,
                        Proposicao.fonte == FonteEnum.CAMARA,
                    )
                ).scalar_one_or_none()

                if existing:
                    stats["ja_existentes"] += 1
                    # Atualizar classificação se estava vazia
                    if not existing.categorias_zil and prop.ementa:
                        cats = classificar_proposicao(ementa=prop.ementa)
                        if cats:
                            existing.categorias_zil = cats
                            existing.relevancia_zil = relevancia_score(prop.ementa, cats)
                            stats["classificadas_zil"] += 1
                    continue

                # Classificar localmente antes de buscar detalhes
                cats_preview = classificar_proposicao(ementa=prop.ementa or "")

                if not cats_preview:
                    # A API retornou pela keyword mas o classificador local não confirma.
                    # Buscar detalhes para ter mais texto e tentar novamente.
                    pass

                # Buscar detalhes completos
                try:
                    detalhes = client.obter_proposicao(prop.id)
                    time.sleep(0.3)  # Rate limiting
                except Exception as e:
                    logger.warning(f"  Erro ao buscar detalhes de {prop.id}: {e}")
                    stats["erros"] += 1
                    continue

                if not detalhes:
                    continue

                ementa = detalhes.get("ementa") or prop.ementa or ""
                ementa_detalhada = detalhes.get("ementaDetalhada") or ""
                keywords_api = detalhes.get("keywords") or ""

                # Classificar com texto completo
                cats = classificar_proposicao(
                    ementa=ementa,
                    ementa_detalhada=ementa_detalhada,
                    indexacao=keywords_api,
                )

                if not cats:
                    # Não classificou em nenhuma categoria ZIL — pular
                    continue

                stats["classificadas_zil"] += 1
                relevancia = relevancia_score(
                    f"{ementa} {ementa_detalhada} {keywords_api}", cats
                )

                if dry_run:
                    tipo = detalhes.get("siglaTipo", "?")
                    numero = detalhes.get("numero", "?")
                    ano = detalhes.get("ano", "?")
                    logger.info(f"  [DRY-RUN] {tipo} {numero}/{ano} — {cats} — {ementa[:80]}...")
                    stats["novas"] += 1
                    continue

                # Extrair dados completos
                status_prop = detalhes.get("statusProposicao") or {}
                data_apres = detalhes.get("dataApresentacao")
                url_teor = detalhes.get("urlInteiroTeor")

                proposicao = Proposicao(
                    fonte_id=fonte_id,
                    fonte=FonteEnum.CAMARA,
                    tipo=detalhes.get("siglaTipo") or prop.siglaTipo,
                    numero=detalhes.get("numero") or prop.numero,
                    ano=detalhes.get("ano") or prop.ano,
                    ementa=ementa,
                    ementa_detalhada=ementa_detalhada if ementa_detalhada else None,
                    situacao=status_prop.get("descricaoSituacao"),
                    data_apresentacao=date.fromisoformat(data_apres[:10]) if data_apres else None,
                    ultimo_despacho=status_prop.get("despacho"),
                    categorias_zil=cats,
                    relevancia_zil=relevancia,
                    classificacao_automatica=True,
                    url_inteiro_teor=url_teor,
                    contexto_status="pendente" if enriquecer else None,
                )

                db.add(proposicao)
                stats["novas"] += 1

                logger.info(
                    f"  + {proposicao.tipo} {proposicao.numero}/{proposicao.ano} "
                    f"— {cats} (rel={relevancia:.2f})"
                )

            # Commit por grupo para não perder progresso
            if not dry_run:
                db.commit()

            # Pausa entre grupos para respeitar rate limits
            time.sleep(1.0)

    finally:
        client.close()

    if not dry_run:
        db.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Descoberta de proposições ZIL")
    parser.add_argument("--ano-inicio", type=int, default=2020, help="Ano inicial (default: 2020)")
    parser.add_argument("--ano-fim", type=int, default=None, help="Ano final (default: ano corrente)")
    parser.add_argument("--enriquecer", action="store_true", help="Marcar novas para enriquecimento")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostrar, sem persistir")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logger.info("=" * 60)
    logger.info("ZIL — Descoberta de Proposições")
    logger.info(f"Período: {args.ano_inicio}–{args.ano_fim or date.today().year}")
    logger.info(f"Enriquecer: {args.enriquecer}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)

    with SessionLocal() as db:
        stats = discover(
            db,
            ano_inicio=args.ano_inicio,
            ano_fim=args.ano_fim,
            enriquecer=args.enriquecer,
            dry_run=args.dry_run,
        )

    logger.info("\n" + "=" * 60)
    logger.info("Resultado da descoberta:")
    logger.info(f"  Total buscadas na API: {stats['total_buscadas']}")
    logger.info(f"  Já existentes no banco: {stats['ja_existentes']}")
    logger.info(f"  Novas classificadas ZIL: {stats['classificadas_zil']}")
    logger.info(f"  Novas persistidas: {stats['novas']}")
    logger.info(f"  Erros: {stats['erros']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
