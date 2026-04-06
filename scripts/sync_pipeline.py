#!/usr/bin/env python3
"""
Pipeline orchestrator: discovery → votação sync → enrichment → scoring.

Runs all 4 pipeline steps in sequence. Each step is idempotent and can
be skipped via CLI flags. Partial failures are logged but don't abort
the pipeline.

Usage:
    python scripts/sync_pipeline.py [OPTIONS]

Options:
    --skip-discovery     Skip Step 1 (proposição discovery)
    --skip-votacoes      Skip Step 2 (votação sync)
    --skip-enrichment    Skip Step 3 (LLM enrichment)
    --skip-scores        Skip Step 4 (score recalculation)
    --dry-run            Dry-run all steps
    --ano-inicio N       Start year for discovery (default: 2020)
    --ano-fim N          End year for discovery (default: current year)

See: specs/002-legislative-enrichment-pipeline/contracts/api.md
"""

import argparse
import logging
import sys
import traceback
from pathlib import Path
from uuid import UUID

# Add repo root + apps/api to sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import Session

from core.config import settings

logger = logging.getLogger(__name__)


def step1_discover(db: Session, ano_inicio: int, ano_fim: int | None, dry_run: bool) -> dict:
    """Step 1: Discover proposições via keyword search."""
    from scripts.discover_proposicoes import discover

    print("\n" + "=" * 60)
    print("STEP 1: Descoberta de proposições")
    print("=" * 60)

    result = discover(
        db=db,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        enriquecer=True,
        dry_run=dry_run,
    )
    return result


def step1_5_sync_detalhes(db: Session, dry_run: bool) -> dict:
    """Step 1.5: Sync detail fields for proposicoes (Feature 012)."""
    from scripts.sync_detalhes_proposicoes import sync_fase1

    print("\n" + "=" * 60)
    print("STEP 1.5: Sync de detalhes de proposicoes")
    print("=" * 60)

    from packages.camara_client import CamaraClient
    with CamaraClient() as client:
        result = sync_fase1(db, client, dry_run)
    return result


def step2_sync_votacoes(db: Session, dry_run: bool) -> dict:
    """Step 2: Sync votações for each proposição."""
    from scripts.sync_votacoes_proposicoes import sync_votacoes_por_proposicao

    print("\n" + "=" * 60)
    print("STEP 2: Sync de votações por proposição")
    print("=" * 60)

    result = sync_votacoes_por_proposicao(
        db=db,
        skip_existing=True,
        dry_run=dry_run,
    )
    return result


def step3_enrich(db: Session, dry_run: bool) -> dict:
    """Step 3: Enrich pending proposições via LLM."""
    from models import Proposicao
    from apps.workers.enrichment import enriquecer_proposicao

    print("\n" + "=" * 60)
    print("STEP 3: Enriquecimento LLM de proposições pendentes")
    print("=" * 60)

    ids = db.execute(
        select(Proposicao.id).where(
            or_(
                Proposicao.contexto_status == "pendente",
                Proposicao.contexto_status.is_(None),
            ),
            Proposicao.categorias_zil.isnot(None),
        )
    ).scalars().all()

    if not ids:
        print("  Nenhuma proposição pendente de enriquecimento.")
        return {"total": 0, "enriquecidas": 0, "erros": 0}

    print(f"  {len(ids)} proposições pendentes de enriquecimento")
    if dry_run:
        print("  [DRY RUN — enriquecimento não será executado]")
        return {"total": len(ids), "enriquecidas": 0, "erros": 0, "dry_run": True}

    enriquecidas = 0
    erros = 0

    for i, pid in enumerate(ids):
        try:
            pid_uuid = UUID(pid) if isinstance(pid, str) and len(pid) == 32 else pid
            result = enriquecer_proposicao(pid_uuid, db)
            enriquecidas += 1
            print(f"  [{i + 1}/{len(ids)}] {result}")
        except Exception as e:
            erros += 1
            logger.warning(f"  [{i + 1}/{len(ids)}] Erro: {e}")

    return {"total": len(ids), "enriquecidas": enriquecidas, "erros": erros}


def step4_scores(db: Session, dry_run: bool) -> dict:
    """Step 4: Apply directions + recalculate scores."""
    from scripts.apply_direcoes import load_direcoes, apply_direcoes
    from apps.workers.scoring import recalcular_todos_scores

    print("\n" + "=" * 60)
    print("STEP 4: Aplicar direções + recalcular scores")
    print("=" * 60)

    data_dir = Path(__file__).parent.parent / "data" / "direcoes"

    if not data_dir.exists():
        print("  Diretório data/direcoes/ não encontrado — pulando direções.")
        direcoes = []
    else:
        direcoes = load_direcoes(data_dir)

    dir_stats = {"matched": 0, "updated": 0, "skipped": 0, "not_found": 0}
    if direcoes:
        print(f"  {len(direcoes)} direções carregadas")
        dir_stats = apply_direcoes(direcoes, db, dry_run=dry_run)
        if not dry_run:
            db.commit()
        print(
            f"  Direções: matched={dir_stats['matched']} "
            f"updated={dir_stats['updated']} "
            f"not_found={dir_stats['not_found']}"
        )
    else:
        print("  Nenhuma direção para aplicar.")

    score_count = 0
    if not dry_run:
        score_count = recalcular_todos_scores(db)
        db.commit()
        print(f"  {score_count} scores recalculados")
    else:
        print("  [DRY RUN — scores não serão recalculados]")

    return {
        "direcoes": dir_stats,
        "scores_recalculados": score_count,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline orchestrator: discovery → votações → enrichment → scoring"
    )
    parser.add_argument(
        "--skip-discovery",
        action="store_true",
        help="Skip Step 1 (proposição discovery)",
    )
    parser.add_argument(
        "--skip-detalhes",
        action="store_true",
        help="Skip Step 1.5 (detail fields sync)",
    )
    parser.add_argument(
        "--skip-votacoes",
        action="store_true",
        help="Skip Step 2 (votação sync)",
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip Step 3 (LLM enrichment)",
    )
    parser.add_argument(
        "--skip-scores",
        action="store_true",
        help="Skip Step 4 (score recalculation)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run all steps",
    )
    parser.add_argument(
        "--ano-inicio",
        type=int,
        default=2020,
        help="Start year for discovery (default: 2020)",
    )
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="End year for discovery (default: current year)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    engine = create_engine(settings.DATABASE_URL)
    results = {}

    with Session(engine) as db:
        # Step 1: Discovery
        if not args.skip_discovery:
            try:
                results["discovery"] = step1_discover(
                    db, args.ano_inicio, args.ano_fim, args.dry_run
                )
            except Exception as e:
                logger.error(f"Step 1 falhou: {e}")
                traceback.print_exc()
                results["discovery"] = {"error": str(e)}
        else:
            print("\n⏭  Step 1: Discovery — PULADO")

        # Step 1.5: Detail fields sync (Feature 012)
        if not args.skip_detalhes:
            try:
                results["detalhes"] = step1_5_sync_detalhes(db, args.dry_run)
            except Exception as e:
                logger.error(f"Step 1.5 falhou: {e}")
                traceback.print_exc()
                results["detalhes"] = {"error": str(e)}
        else:
            print("\n⏭  Step 1.5: Detail sync — PULADO")

        # Step 2: Votação sync
        if not args.skip_votacoes:
            try:
                results["votacoes"] = step2_sync_votacoes(db, args.dry_run)
            except Exception as e:
                logger.error(f"Step 2 falhou: {e}")
                traceback.print_exc()
                results["votacoes"] = {"error": str(e)}
        else:
            print("\n⏭  Step 2: Votação sync — PULADO")

        # Step 3: Enrichment
        if not args.skip_enrichment:
            try:
                results["enrichment"] = step3_enrich(db, args.dry_run)
            except Exception as e:
                logger.error(f"Step 3 falhou: {e}")
                traceback.print_exc()
                results["enrichment"] = {"error": str(e)}
        else:
            print("\n⏭  Step 3: Enrichment — PULADO")

        # Step 4: Scores
        if not args.skip_scores:
            try:
                results["scores"] = step4_scores(db, args.dry_run)
            except Exception as e:
                logger.error(f"Step 4 falhou: {e}")
                traceback.print_exc()
                results["scores"] = {"error": str(e)}
        else:
            print("\n⏭  Step 4: Scores — PULADO")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMO DO PIPELINE")
    print("=" * 60)
    for step_name, step_result in results.items():
        if "error" in step_result:
            print(f"  {step_name}: FALHOU — {step_result['error']}")
        else:
            print(f"  {step_name}: OK — {step_result}")

    if args.dry_run:
        print("\n[DRY RUN — nenhuma mudança foi gravada]")


if __name__ == "__main__":
    main()
