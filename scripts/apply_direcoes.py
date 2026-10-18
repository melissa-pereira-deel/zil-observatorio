#!/usr/bin/env python3
"""
Apply direcao_esperada from data/direcoes/<ano>.yml to the database.

Usage:
    python scripts/apply_direcoes.py [--ano 2024] [--dry-run]

Reads all data/direcoes/*.yml files (or a specific year) and updates
Votacao.direcao_esperada and Votacao.peso for each matched votação.

Matching: votacao.fonte_id == direcao.fonte_id AND votacao.fonte == direcao.fonte
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add repo root + apps/api to sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from core.config import settings
from models import Votacao, Voto
from apps.workers.scoring import recalcular_todos_scores


def load_direcoes(data_dir: Path, ano: int | None = None) -> list[dict]:
    """Load all direcoes from YAML files."""
    files = sorted(data_dir.glob("*.yml"))
    if ano:
        files = [f for f in files if f.stem == str(ano)]

    all_direcoes = []
    for f in files:
        with open(f) as fh:
            data = yaml.safe_load(fh)
        direcoes = data.get("direcoes") or []
        for d in direcoes:
            d["_source_file"] = f.name
        all_direcoes.extend(direcoes)

    return all_direcoes


def apply_direcoes(direcoes: list[dict], db: Session, dry_run: bool = False) -> dict:
    stats = {"matched": 0, "not_found": 0, "updated": 0, "skipped": 0,
             "simbolicas": 0}

    for d in direcoes:
        fonte_id = str(d["fonte_id"])
        fonte = d["fonte"]
        direcao = d["direcao"]
        peso = float(d.get("peso", 1.0))

        votacao = db.execute(
            select(Votacao).where(
                Votacao.fonte_id == fonte_id,
                Votacao.fonte == fonte,
            )
        ).scalar_one_or_none()

        if not votacao:
            print(f"  NOT FOUND: {fonte}:{fonte_id} [{d['_source_file']}]")
            stats["not_found"] += 1
            continue

        stats["matched"] += 1

        # Este é o último ponto antes de a curadoria virar Score ZIL, e é onde
        # dá para notar que ela não vai virar nada: votação simbólica (RICD
        # art. 185) não registra voto individual, então direção e peso não têm
        # sobre o que incidir. Três das sete entradas curadas eram assim, com
        # peso 3.0, 3.0 e 2.0, e ninguém percebeu.
        n_votos = db.execute(
            select(func.count()).select_from(Voto).where(Voto.votacao_id == votacao.id)
        ).scalar_one()
        if n_votos == 0:
            stats["simbolicas"] += 1
            declarado = (d.get("processo") or "não declarado")
            print(
                f"  ⚠ {fonte}:{fonte_id} não tem voto individual — votação "
                f"simbólica, não contribui para o Score ZIL "
                f"(processo: {declarado})"
            )

        if votacao.direcao_esperada == direcao and votacao.peso == peso:
            stats["skipped"] += 1
            continue

        print(
            f"  UPDATE {fonte}:{fonte_id} "
            f"direcao={direcao} peso={peso} "
            f"(was: {votacao.direcao_esperada}/{votacao.peso})"
        )

        if not dry_run:
            votacao.direcao_esperada = direcao
            votacao.peso = peso
            stats["updated"] += 1
        else:
            stats["updated"] += 1  # count as would-update in dry-run

    return stats


def main():
    parser = argparse.ArgumentParser(description="Apply direcoes_esperadas to database")
    parser.add_argument("--ano", type=int, help="Year to process (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without applying")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data" / "direcoes"
    if not data_dir.exists():
        print(f"ERROR: {data_dir} not found")
        sys.exit(1)

    direcoes = load_direcoes(data_dir, args.ano)

    if not direcoes:
        print("No direcoes to apply (all files have empty lists).")
        return

    print(f"Loaded {len(direcoes)} direcoes from {data_dir}")
    if args.dry_run:
        print("[DRY RUN — no changes will be written]")

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        stats = apply_direcoes(direcoes, db, dry_run=args.dry_run)
        if not args.dry_run:
            db.commit()

        # Recalculate scores after applying directions (FR-016)
        if not args.dry_run and stats["updated"] > 0:
            score_count = recalcular_todos_scores(db)
            db.commit()
            print(f"\n{score_count} scores recalculados")

    print(
        f"\nDone. matched={stats['matched']} updated={stats['updated']} "
        f"skipped={stats['skipped']} not_found={stats['not_found']}"
    )

    if stats["simbolicas"]:
        alimentam = stats["matched"] - stats["simbolicas"]
        print(
            f"\n⚠ {stats['simbolicas']} das {stats['matched']} votações curadas "
            f"são simbólicas e não produzem voto individual. O Score ZIL se "
            f"apoia em {alimentam}, não em {stats['matched']}."
        )


if __name__ == "__main__":
    main()
