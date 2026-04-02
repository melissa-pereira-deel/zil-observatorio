"""Contract tests: verify response shapes match API contracts."""

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tests.conftest import make_parlamentar, make_votacao, make_voto, make_proposicao
from models import VotoEnum


def test_schema_parlamentar_ranking(client, db_session):
    """ParlamentarRanking deve ter todos os campos do contrato."""
    make_parlamentar(db_session, score_zil=5.5)
    db_session.commit()

    resp = client.get("/parlamentares")
    assert resp.status_code == 200
    item = resp.json()[0]

    required_fields = {"id", "nome", "partido", "uf", "fonte", "score_zil", "total_votos_zil"}
    assert required_fields.issubset(item.keys()), f"Campos ausentes: {required_fields - item.keys()}"

    assert isinstance(item["id"], str)
    assert isinstance(item["nome"], str)
    assert isinstance(item["total_votos_zil"], int)
    # score_zil pode ser null
    assert item["score_zil"] is None or isinstance(item["score_zil"], float)


def test_schema_parlamentar_read(client, db_session):
    """ParlamentarRead deve ter todos os campos do contrato."""
    p = make_parlamentar(db_session, score_zil=3.2)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}")
    assert resp.status_code == 200
    item = resp.json()

    required_fields = {"id", "fonte_id", "fonte", "nome", "partido", "uf"}
    assert required_fields.issubset(item.keys())


def test_schema_voto_historico(client, db_session):
    """VotoHistorico deve ter todos os campos do contrato."""
    p = make_parlamentar(db_session)
    v = make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim")
    make_voto(db_session, p, v, VotoEnum.SIM)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil")
    assert resp.status_code == 200
    item = resp.json()[0]

    required_fields = {"votacao_id", "data", "descricao", "categorias_zil", "voto", "direcao_esperada", "alinhado"}
    assert required_fields.issubset(item.keys()), f"Campos ausentes: {required_fields - item.keys()}"

    assert isinstance(item["voto"], str)
    assert item["alinhado"] in (True, False, None)


def test_schema_proposicao_read(client, db_session):
    """ProposicaoRead deve ter todos os campos do contrato."""
    make_proposicao(db_session, categorias_zil=["ZIL-FER"])
    db_session.commit()

    resp = client.get("/proposicoes")
    assert resp.status_code == 200
    item = resp.json()[0]

    required_fields = {"id", "fonte_id", "tipo", "numero", "ano", "ementa", "categorias_zil"}
    assert required_fields.issubset(item.keys()), f"Campos ausentes: {required_fields - item.keys()}"

    assert isinstance(item["categorias_zil"], list)


def test_schema_votacao_read(client, db_session):
    """VotacaoRead deve ter todos os campos do contrato."""
    make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="sim")
    db_session.commit()

    resp = client.get("/votacoes")
    assert resp.status_code == 200
    item = resp.json()[0]

    required_fields = {"id", "fonte_id", "data", "descricao", "resultado", "categorias_zil", "peso"}
    assert required_fields.issubset(item.keys()), f"Campos ausentes: {required_fields - item.keys()}"

    assert item["peso"] is None or isinstance(item["peso"], (int, float))


def test_schema_voto_read(client, db_session):
    """VotoRead deve ter todos os campos do contrato."""
    p = make_parlamentar(db_session, partido="PT", uf="SP")
    v = make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    make_voto(db_session, p, v, VotoEnum.NAO)
    db_session.commit()

    resp = client.get(f"/votacoes/{v.id}/votos")
    assert resp.status_code == 200
    item = resp.json()[0]

    required_fields = {"parlamentar_id", "parlamentar_nome", "parlamentar_partido", "parlamentar_uf", "voto"}
    assert required_fields.issubset(item.keys())

    assert item["voto"] in ("sim", "nao", "abstencao", "ausente", "obstrucao", "artigo_17")


def test_sem_autenticacao_requerida(client, db_session):
    """Nenhum endpoint deve exigir autenticação (Princípio I)."""
    make_parlamentar(db_session, score_zil=1.0)
    make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    make_proposicao(db_session, categorias_zil=["ZIL-FER"])
    db_session.commit()

    endpoints = [
        "/parlamentares",
        "/proposicoes",
        "/votacoes",
        "/stats",
    ]
    for endpoint in endpoints:
        resp = client.get(endpoint)
        assert resp.status_code != 401, f"Endpoint {endpoint} retornou 401 (autenticação exigida)"
        assert resp.status_code != 403, f"Endpoint {endpoint} retornou 403 (acesso negado)"
