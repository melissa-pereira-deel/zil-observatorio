"""Migrations do Alembic em SQLite temporário: sobem, descem e batem com o modelo.

O `Config()` é montado sem arquivo `.ini` de propósito. Com arquivo, o `env.py`
chama `fileConfig`, que desliga os loggers já existentes e quebra o `caplog` de
`tests/unit/test_bussula.py` quando a suíte roda inteira.
"""

import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from core.config import Base  # noqa: E402
import models  # noqa: E402,F401  — registra as tabelas em Base.metadata

# O head de antes de TRM-011. Ids de revisão são hex por convenção, não segredo.
REVISAO_ANTERIOR = "b81e4c07d2a9"  # pragma: allowlist secret

# Bloco TRM-011 de specs/013-tramitacao/backlog-dados.md §1.3.
COLUNAS_TRM_011 = {
    "cod_situacao",
    "sigla_orgao",
    "orgao_fonte_id",
    "orgao_nome",
    "orgao_tipo_cod",
    "cod_tipo_tramitacao",
    "descricao_tramitacao",
    "regime",
    "apreciacao",
    "status_sequencia",
    "status_url",
    "status_bruto",
    "ultima_movimentacao_em",
    "relator_fonte_id",
    "relator_nome",
    "principal_fonte_id",
    "orgao_efetivo_sigla",
    "orgao_efetivo_nome",
    "detalhe_sincronizado_em",
    "origem_registro",
    "norma_tipo",
    "norma_numero",
    "norma_ano",
    "norma_data",
    "norma_veto",
    "norma_fonte",
    "norma_tramitacao_sequencia",
    "norma_verificada_em",
}
INDICES_TRM_011 = {
    "ix_proposicao_ultima_mov": ["ultima_movimentacao_em"],
    "ix_proposicao_cod_situacao": ["cod_situacao"],
    "ix_proposicao_principal_fonte": ["principal_fonte_id"],
}

# O que `compare_metadata` reporta como objeto faltando ou sobrando. Diferença
# de tipo fica de fora: o SQLite reflete tipos de forma aproximada.
DIFERENCAS_ESTRUTURAIS = {
    "add_table",
    "remove_table",
    "add_column",
    "remove_column",
    "add_index",
    "remove_index",
}


def _config(db_url: str) -> Config:
    cfg = Config()  # sem .ini: fileConfig não roda e não desliga os loggers dos outros testes
    cfg.set_main_option("script_location", str(API_DIR / "data" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture
def db_url(tmp_path, monkeypatch) -> str:
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)  # env.py lê DATABASE_URL na hora
    return url


def _colunas_proposicoes(url: str) -> dict[str, dict]:
    engine = create_engine(url)
    try:
        return {c["name"]: c for c in inspect(engine).get_columns("proposicoes")}
    finally:
        engine.dispose()


def _indices_proposicoes(url: str) -> dict[str, list[str]]:
    engine = create_engine(url)
    try:
        return {i["name"]: i["column_names"] for i in inspect(engine).get_indexes("proposicoes")}
    finally:
        engine.dispose()


def test_sobe_desce_sobe(db_url):
    cfg = _config(db_url)

    command.upgrade(cfg, "head")
    colunas = _colunas_proposicoes(db_url)
    indices = _indices_proposicoes(db_url)
    assert COLUNAS_TRM_011 <= set(colunas)
    assert all(colunas[nome]["nullable"] for nome in COLUNAS_TRM_011)
    assert INDICES_TRM_011.items() <= indices.items()

    command.downgrade(cfg, REVISAO_ANTERIOR)
    assert not COLUNAS_TRM_011 & set(_colunas_proposicoes(db_url))
    assert not set(INDICES_TRM_011) & set(_indices_proposicoes(db_url))

    command.upgrade(cfg, "head")
    assert COLUNAS_TRM_011 <= set(_colunas_proposicoes(db_url))
    assert INDICES_TRM_011.items() <= _indices_proposicoes(db_url).items()


def test_descer_preserva_linhas_e_colunas_antigas(db_url):
    """No SQLite, `drop_column` em batch recria a tabela; as linhas têm de sobreviver."""
    cfg = _config(db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO proposicoes (id, fonte_id, fonte, situacao, classificacao_automatica, created_at) "
                    "VALUES ('00000000000000000000000000000001', '123', 'CAMARA', 'Pronta para Pauta', 1, "
                    "'2026-01-01 00:00:00.000000')"
                )
            )
    finally:
        engine.dispose()

    command.downgrade(cfg, REVISAO_ANTERIOR)

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            linhas = conn.execute(text("SELECT fonte_id, situacao, tramitacoes FROM proposicoes")).all()
        indices = {i["name"] for i in inspect(engine).get_indexes("proposicoes")}
        unicas = {u["name"] for u in inspect(engine).get_unique_constraints("proposicoes")}
    finally:
        engine.dispose()
    assert [tuple(linha) for linha in linhas] == [("123", "Pronta para Pauta", None)]
    assert {"ix_proposicao_tipo_ano", "ix_proposicao_contexto_status"} <= indices
    assert "uq_proposicao_fonte" in unicas


def test_modelo_bate_com_migrations(db_url):
    command.upgrade(_config(db_url), "head")

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()

    estruturais = [d for d in diffs if isinstance(d, tuple) and d[0] in DIFERENCAS_ESTRUTURAIS]
    assert estruturais == []
