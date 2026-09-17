"""Ambiente de migrations do Alembic.

A URL do banco vem de DATABASE_URL (ambiente), não do alembic.ini: credenciais
não devem ficar versionadas, e produção precisa apontar para outro banco sem
editar arquivo. O alembic.ini mantém apenas um fallback de desenvolvimento.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# apps/api precisa estar no sys.path para os imports curtos do projeto
# (`from models import ...`), conforme ADR-002.
_API_DIR = Path(__file__).resolve().parents[2]
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from core.config import Base  # noqa: E402
import models  # noqa: E402,F401  — registra as 8 tabelas em Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """DATABASE_URL do ambiente, com fallback para o alembic.ini."""
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "DATABASE_URL não definida e nenhum sqlalchemy.url no alembic.ini"
        )
    return url


def run_migrations_offline() -> None:
    """Gera SQL sem conectar ao banco (alembic upgrade head --sql)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations conectando ao banco."""
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
