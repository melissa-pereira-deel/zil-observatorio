#!/usr/bin/env python3
"""
Migration: add Feature 002 enrichment fields to existing databases.

Safe to run multiple times (idempotent — skips columns/tables that already exist).

Usage:
    python3 scripts/migrate_enrichment.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

# ADR-002: add apps/api to sys.path
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from sqlalchemy import create_engine, inspect, text
from core.config import settings


NEW_PROPOSICOES_COLUMNS = [
    ("contexto_status",  "VARCHAR(20)"),
    ("resumo_simples",   "TEXT"),
    ("glossario",        "TEXT"),   # JSON stored as TEXT in SQLite
    ("impacto_zil",      "TEXT"),
    ("leis_referenciadas", "TEXT"), # JSON stored as TEXT in SQLite
    ("confianca",        "NUMERIC(3,2)"),
    ("ementa_hash",      "VARCHAR(64)"),
    ("enriquecido_em",   "DATETIME"),
]

CREATE_LEI_ARTIGOS = """
CREATE TABLE IF NOT EXISTS lei_artigos (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    lei_id VARCHAR(50) NOT NULL,
    numero_artigo VARCHAR(20) NOT NULL,
    texto_artigo TEXT,
    url_planalto VARCHAR(500),
    status VARCHAR(30) NOT NULL DEFAULT 'resolvido',
    obtido_em DATETIME NOT NULL,
    expira_em DATETIME NOT NULL,
    UNIQUE (lei_id, numero_artigo)
);
"""

CREATE_INDEX_LEI_ARTIGO_LEI_ID = (
    "CREATE INDEX IF NOT EXISTS ix_lei_artigo_lei_id ON lei_artigos (lei_id);"
)
CREATE_INDEX_LEI_ARTIGO_EXPIRA = (
    "CREATE INDEX IF NOT EXISTS ix_lei_artigo_expira_em ON lei_artigos (expira_em);"
)
CREATE_INDEX_PROPOSICAO_CONTEXTO = (
    "CREATE INDEX IF NOT EXISTS ix_proposicao_contexto_status ON proposicoes (contexto_status);"
)


def run(dry_run: bool = False) -> None:
    engine = create_engine(settings.DATABASE_URL)
    insp = inspect(engine)

    with engine.connect() as conn:
        # 1 — Create lei_artigos table
        if "lei_artigos" not in insp.get_table_names():
            print("Creating table: lei_artigos")
            if not dry_run:
                conn.execute(text(CREATE_LEI_ARTIGOS))
                conn.execute(text(CREATE_INDEX_LEI_ARTIGO_LEI_ID))
                conn.execute(text(CREATE_INDEX_LEI_ARTIGO_EXPIRA))
                conn.commit()
        else:
            print("Table lei_artigos already exists — skipping.")

        # 2 — Add new columns to proposicoes
        existing_cols = {c["name"] for c in insp.get_columns("proposicoes")}
        for col_name, col_type in NEW_PROPOSICOES_COLUMNS:
            if col_name in existing_cols:
                print(f"  Column proposicoes.{col_name} already exists — skipping.")
                continue
            print(f"  Adding column: proposicoes.{col_name} {col_type}")
            if not dry_run:
                conn.execute(
                    text(f"ALTER TABLE proposicoes ADD COLUMN {col_name} {col_type};")
                )
                conn.commit()

        # 3 — Add index on contexto_status
        existing_indexes = {ix["name"] for ix in insp.get_indexes("proposicoes")}
        if "ix_proposicao_contexto_status" not in existing_indexes:
            print("Creating index: ix_proposicao_contexto_status")
            if not dry_run:
                conn.execute(text(CREATE_INDEX_PROPOSICAO_CONTEXTO))
                conn.commit()
        else:
            print("Index ix_proposicao_contexto_status already exists — skipping.")

    if dry_run:
        print("\n[DRY RUN — no changes applied]")
    else:
        print("\nMigration complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature 002 enrichment migration")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without applying")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
