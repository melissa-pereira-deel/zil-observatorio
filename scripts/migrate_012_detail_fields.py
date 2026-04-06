#!/usr/bin/env python3
"""
Migration: Feature 012 — Enriquecimento de Dados de Proposicoes.

Adds new columns to proposicoes and votacoes, creates new tables
(proposicao_autores, proposicao_relacoes).

Safe to run multiple times (idempotent — skips columns/tables that already exist).

Usage:
    python3 scripts/migrate_012_detail_fields.py [--dry-run] [--fase 1|2|3]
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


# ── Phase 1: New columns on existing tables ──

PHASE1_PROPOSICOES_COLUMNS = [
    ("cod_situacao",              "INTEGER"),
    ("regime",                    "VARCHAR(50)"),
    ("apreciacao",                "VARCHAR(100)"),
    ("keywords_camara",           "TEXT"),
    ("urn_final",                 "VARCHAR(500)"),
    ("detalhes_sincronizados_em", "DATETIME"),
]

PHASE1_VOTACOES_COLUMNS = [
    ("aprovacao",          "INTEGER"),
    ("sigla_orgao",        "VARCHAR(20)"),
    ("proposicao_objeto",  "TEXT"),
]

PHASE1_INDEXES = [
    ("ix_proposicao_cod_situacao",  "proposicoes", "cod_situacao"),
    ("ix_proposicao_regime",        "proposicoes", "regime"),
    ("ix_proposicao_detalhes_sync", "proposicoes", "detalhes_sincronizados_em"),
]


# ── Phase 2: proposicao_autores table + temas column ──

PHASE2_PROPOSICOES_COLUMNS = [
    ("temas_camara", "TEXT"),  # JSON stored as TEXT (ADR-001)
]

CREATE_PROPOSICAO_AUTORES = """
CREATE TABLE IF NOT EXISTS proposicao_autores (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    proposicao_id VARCHAR(36) NOT NULL REFERENCES proposicoes(id) ON DELETE CASCADE,
    parlamentar_id VARCHAR(36) REFERENCES parlamentares(id),
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 1,
    proponente BOOLEAN NOT NULL DEFAULT 1,
    uri_autor VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (proposicao_id, ordem)
);
"""

PHASE2_INDEXES = [
    ("ix_autor_parlamentar", "proposicao_autores", "parlamentar_id"),
    ("ix_autor_proposicao",  "proposicao_autores", "proposicao_id"),
]


# ── Phase 3: proposicao_relacoes table + cadeia/orgao columns ──

PHASE3_PROPOSICOES_COLUMNS = [
    ("prop_principal_id", "VARCHAR(50)"),
    ("prop_anterior_id",  "VARCHAR(50)"),
    ("prop_posterior_id", "VARCHAR(50)"),
    ("orgao_situacao",    "VARCHAR(50)"),
    ("relator_id",        "VARCHAR(36) REFERENCES parlamentares(id)"),
]

CREATE_PROPOSICAO_RELACOES = """
CREATE TABLE IF NOT EXISTS proposicao_relacoes (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    proposicao_id VARCHAR(36) NOT NULL REFERENCES proposicoes(id) ON DELETE CASCADE,
    relacionada_id VARCHAR(36) REFERENCES proposicoes(id),
    relacionada_fonte_id VARCHAR(50) NOT NULL,
    tipo_relacao VARCHAR(30) NOT NULL,
    sigla_tipo VARCHAR(20),
    numero INTEGER,
    ano INTEGER,
    ementa TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (proposicao_id, relacionada_fonte_id)
);
"""

PHASE3_INDEXES = [
    ("ix_relacao_proposicao",  "proposicao_relacoes", "proposicao_id"),
    ("ix_relacao_relacionada", "proposicao_relacoes", "relacionada_id"),
    ("ix_relacao_tipo",        "proposicao_relacoes", "tipo_relacao"),
]


def _add_columns(conn, insp, table: str, columns: list[tuple[str, str]], dry_run: bool) -> None:
    """Add columns to a table if they don't exist."""
    existing = {c["name"] for c in insp.get_columns(table)}
    for col_name, col_type in columns:
        if col_name in existing:
            print(f"  Column {table}.{col_name} already exists — skipping.")
            continue
        print(f"  Adding column: {table}.{col_name} {col_type}")
        if not dry_run:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type};"))
            conn.commit()


def _create_indexes(conn, insp, indexes: list[tuple[str, str, str]], dry_run: bool) -> None:
    """Create indexes if they don't exist."""
    for idx_name, table, column in indexes:
        existing_indexes = {ix["name"] for ix in insp.get_indexes(table)}
        if idx_name in existing_indexes:
            print(f"  Index {idx_name} already exists — skipping.")
            continue
        print(f"  Creating index: {idx_name} on {table}({column})")
        if not dry_run:
            conn.execute(text(f"CREATE INDEX {idx_name} ON {table} ({column});"))
            conn.commit()


def run_phase1(conn, insp, dry_run: bool) -> None:
    """Phase 1: Add detail columns to proposicoes and votacoes."""
    print("\n=== Phase 1: Detail columns ===")

    print("Adding columns to proposicoes...")
    _add_columns(conn, insp, "proposicoes", PHASE1_PROPOSICOES_COLUMNS, dry_run)

    print("Adding columns to votacoes...")
    _add_columns(conn, insp, "votacoes", PHASE1_VOTACOES_COLUMNS, dry_run)

    print("Creating indexes...")
    _create_indexes(conn, insp, PHASE1_INDEXES, dry_run)

    print("Phase 1 complete.")


def run_phase2(conn, insp, dry_run: bool) -> None:
    """Phase 2: Create proposicao_autores table + temas column."""
    print("\n=== Phase 2: Autores + Temas ===")

    # Create table
    if "proposicao_autores" not in insp.get_table_names():
        print("Creating table: proposicao_autores")
        if not dry_run:
            conn.execute(text(CREATE_PROPOSICAO_AUTORES))
            conn.commit()
    else:
        print("Table proposicao_autores already exists — skipping.")

    # Add temas column
    print("Adding columns to proposicoes...")
    _add_columns(conn, insp, "proposicoes", PHASE2_PROPOSICOES_COLUMNS, dry_run)

    # Create indexes
    print("Creating indexes...")
    _create_indexes(conn, insp, PHASE2_INDEXES, dry_run)

    print("Phase 2 complete.")


def run_phase3(conn, insp, dry_run: bool) -> None:
    """Phase 3: Create proposicao_relacoes table + cadeia/orgao columns."""
    print("\n=== Phase 3: Cadeia + Relacionadas ===")

    # Create table
    if "proposicao_relacoes" not in insp.get_table_names():
        print("Creating table: proposicao_relacoes")
        if not dry_run:
            conn.execute(text(CREATE_PROPOSICAO_RELACOES))
            conn.commit()
    else:
        print("Table proposicao_relacoes already exists — skipping.")

    # Add columns
    print("Adding columns to proposicoes...")
    _add_columns(conn, insp, "proposicoes", PHASE3_PROPOSICOES_COLUMNS, dry_run)

    # Create indexes
    print("Creating indexes...")
    _create_indexes(conn, insp, PHASE3_INDEXES, dry_run)

    print("Phase 3 complete.")


def run(fase: int = 0, dry_run: bool = False) -> None:
    """Run migration for specified phase(s).

    Args:
        fase: Phase number (1, 2, or 3). 0 = all phases.
        dry_run: If True, print changes without applying.
    """
    engine = create_engine(settings.DATABASE_URL)
    insp = inspect(engine)

    with engine.connect() as conn:
        if fase == 0 or fase == 1:
            run_phase1(conn, insp, dry_run)
        if fase == 0 or fase == 2:
            run_phase2(conn, insp, dry_run)
        if fase == 0 or fase == 3:
            run_phase3(conn, insp, dry_run)

    if dry_run:
        print("\n[DRY RUN — no changes applied]")
    else:
        print("\nMigration complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature 012 detail fields migration")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without applying")
    parser.add_argument("--fase", type=int, default=0, choices=[0, 1, 2, 3],
                        help="Phase to run (0=all, 1/2/3=specific)")
    args = parser.parse_args()
    run(fase=args.fase, dry_run=args.dry_run)
