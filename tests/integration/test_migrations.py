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
from sqlalchemy import JSON, Date, DateTime, Integer, String, create_engine, inspect, text
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from core.config import Base  # noqa: E402
from models import FonteEnum, Proposicao  # noqa: E402  — e registra as tabelas em Base.metadata

# O head de antes de TRM-011. Ids de revisão são hex por convenção, não segredo.
REVISAO_ANTERIOR = "b81e4c07d2a9"  # pragma: allowlist secret
REVISAO_TRM_011 = "3a9c5e71b2d4"  # pragma: allowlist secret

# Bloco TRM-011 de specs/013-tramitacao/backlog-dados.md §1.3, escrito à mão de
# propósito: é o contrato contra o qual migration e modelo são conferidos, então
# não pode ser derivado de nenhum dos dois.
COLUNAS_TRM_011 = {
    "cod_situacao": String(10),
    "sigla_orgao": String(30),
    "orgao_fonte_id": String(20),
    "orgao_nome": String(255),
    "orgao_tipo_cod": String(10),
    "cod_tipo_tramitacao": String(10),
    "descricao_tramitacao": String(255),
    "regime": String(255),
    "apreciacao": String(255),
    "status_sequencia": Integer(),
    "status_url": String(500),
    "status_bruto": JSON(none_as_null=True),
    "ultima_movimentacao_em": DateTime(),
    "relator_fonte_id": String(20),
    "relator_nome": String(255),
    "principal_fonte_id": String(20),
    "orgao_efetivo_sigla": String(30),
    "orgao_efetivo_nome": String(255),
    "detalhe_sincronizado_em": DateTime(),
    "origem_registro": String(30),
    "norma_tipo": String(30),
    "norma_numero": Integer(),
    "norma_ano": Integer(),
    "norma_data": Date(),
    "norma_veto": String(10),
    "norma_fonte": String(30),
    "norma_tramitacao_sequencia": Integer(),
    "norma_verificada_em": DateTime(),
}
INDICES_TRM_011 = {
    "ix_proposicao_ultima_mov": ["ultima_movimentacao_em"],
    "ix_proposicao_cod_situacao": ["cod_situacao"],
    "ix_proposicao_principal_fonte": ["principal_fonte_id"],
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


def _tipos(colunas: dict[str, dict]) -> dict[str, str]:
    return {nome: str(coluna["type"]) for nome, coluna in colunas.items()}


def test_sobe_desce_sobe(db_url):
    cfg = _config(db_url)
    command.upgrade(cfg, REVISAO_ANTERIOR)
    colunas_antes = _tipos(_colunas_proposicoes(db_url))
    indices_antes = _indices_proposicoes(db_url)

    command.upgrade(cfg, "head")
    assert COLUNAS_TRM_011.keys() <= _colunas_proposicoes(db_url).keys()
    assert INDICES_TRM_011.items() <= _indices_proposicoes(db_url).items()

    command.downgrade(cfg, REVISAO_ANTERIOR)
    assert _tipos(_colunas_proposicoes(db_url)) == colunas_antes
    assert _indices_proposicoes(db_url) == indices_antes

    command.upgrade(cfg, "head")
    assert COLUNAS_TRM_011.keys() <= _colunas_proposicoes(db_url).keys()
    assert INDICES_TRM_011.items() <= _indices_proposicoes(db_url).items()


def test_trm_011_cria_exatamente_as_colunas_e_indices_da_spec(db_url):
    """Igualdade exata, para pegar tipo errado e coluna ou índice a mais.

    Mede a diferença entre as duas revisões, e não o `head`, para continuar
    valendo quando TRM-027 acrescentar outras colunas a `proposicoes`.
    """
    cfg = _config(db_url)
    command.upgrade(cfg, REVISAO_ANTERIOR)
    colunas_antes = _colunas_proposicoes(db_url)
    indices_antes = _indices_proposicoes(db_url)

    command.upgrade(cfg, REVISAO_TRM_011)
    colunas = _colunas_proposicoes(db_url)
    novas = {nome: coluna for nome, coluna in colunas.items() if nome not in colunas_antes}
    indices = _indices_proposicoes(db_url)

    assert _tipos(novas) == {
        nome: tipo.compile(dialect=sqlite.dialect()) for nome, tipo in COLUNAS_TRM_011.items()
    }
    assert [nome for nome, coluna in novas.items() if not coluna["nullable"]] == []
    assert {nome: alvo for nome, alvo in indices.items() if nome not in indices_antes} == INDICES_TRM_011


def test_modelo_declara_os_tipos_da_spec():
    """O `none_as_null` só existe no modelo: não muda o DDL, então o banco não o mostra."""
    tabela = Proposicao.__table__
    assert {nome: repr(tabela.c[nome].type) for nome in COLUNAS_TRM_011} == {
        nome: repr(tipo) for nome, tipo in COLUNAS_TRM_011.items()
    }
    assert [nome for nome in COLUNAS_TRM_011 if not tabela.c[nome].nullable] == []


def test_none_nas_colunas_json_vira_null_no_banco(db_url):
    """ADR-003: sem `none_as_null`, gravar `None` guarda o JSON `null` e `IS NULL` não acha a linha."""
    command.upgrade(_config(db_url), "head")
    colunas_json = [nome for nome, tipo in COLUNAS_TRM_011.items() if isinstance(tipo, JSON)]
    assert colunas_json

    engine = create_engine(db_url)
    try:
        with Session(engine) as db:
            # None explícito: coluna omitida do INSERT sairia NULL em qualquer configuração.
            criada_nula = Proposicao(fonte_id="1", fonte=FonteEnum.CAMARA, **dict.fromkeys(colunas_json))
            anulada = Proposicao(fonte_id="2", fonte=FonteEnum.CAMARA, **dict.fromkeys(colunas_json, {"a": 1}))
            com_valor = Proposicao(fonte_id="3", fonte=FonteEnum.CAMARA, **dict.fromkeys(colunas_json, {"a": 1}))
            db.add_all([criada_nula, anulada, com_valor])
            db.commit()
            for nome in colunas_json:
                setattr(anulada, nome, None)
            db.commit()

        with engine.connect() as conn:
            for nome in colunas_json:
                nulas = conn.execute(text(f"SELECT fonte_id FROM proposicoes WHERE {nome} IS NULL")).scalars().all()
                assert sorted(nulas) == ["1", "2"], nome
    finally:
        engine.dispose()


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
            contexto = MigrationContext.configure(conn, opts={"compare_type": True})
            diferencas = compare_metadata(contexto, Base.metadata)
    finally:
        engine.dispose()

    # Sem filtro: inclui diferença de tipo, que o SQLite reflete bem para estes
    # tipos. O CI só roda em SQLite, então é aqui que `String` na migration e
    # `Integer` no modelo aparecem antes de chegar ao Postgres.
    assert diferencas == []
