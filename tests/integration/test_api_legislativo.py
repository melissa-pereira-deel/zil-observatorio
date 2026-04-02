"""Integration tests for /proposicoes, /votacoes, and /votacoes/{id}/votos."""

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


# ── GET /proposicoes ──

def test_listar_proposicoes_vazio(client):
    resp = client.get("/proposicoes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_proposicoes_com_dados(client, db_session):
    make_proposicao(db_session, categorias_zil=["ZIL-MIN"])
    make_proposicao(db_session, tipo="PEC", numero=45, categorias_zil=["ZIL-ENE"])
    db_session.commit()

    resp = client.get("/proposicoes")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_filtro_proposicoes_por_categoria(client, db_session):
    make_proposicao(db_session, numero=1, categorias_zil=["ZIL-MIN"])
    make_proposicao(db_session, numero=2, categorias_zil=["ZIL-ENE"])
    db_session.commit()

    resp = client.get("/proposicoes?categoria=ZIL-MIN")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "ZIL-MIN" in data[0]["categorias_zil"]


def test_filtro_proposicoes_por_tipo(client, db_session):
    make_proposicao(db_session, tipo="PL", numero=1, categorias_zil=["ZIL-MIN"])
    make_proposicao(db_session, tipo="PEC", numero=2, categorias_zil=["ZIL-ENE"])
    db_session.commit()

    resp = client.get("/proposicoes?tipo=PL")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "PL"


def test_proposicoes_sem_categoria_nao_aparecem(client, db_session):
    make_proposicao(db_session, numero=1, categorias_zil=["ZIL-MIN"])
    make_proposicao(db_session, numero=2, categorias_zil=None)  # não classificada
    db_session.commit()

    resp = client.get("/proposicoes")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_campos_proposicao_read(client, db_session):
    make_proposicao(db_session, categorias_zil=["ZIL-FER"])
    db_session.commit()

    resp = client.get("/proposicoes")
    item = resp.json()[0]
    for campo in ("id", "fonte_id", "tipo", "numero", "ano", "ementa", "categorias_zil"):
        assert campo in item, f"Campo '{campo}' ausente"


# ── GET /votacoes ──

def test_listar_votacoes_vazio(client):
    resp = client.get("/votacoes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_filtro_votacoes_por_categoria(client, db_session):
    make_votacao(db_session, descricao="V1", categorias_zil=["ZIL-MIN"])
    make_votacao(db_session, descricao="V2", categorias_zil=["ZIL-ENE"])
    make_votacao(db_session, descricao="V3", categorias_zil=None)  # não classificada
    db_session.commit()

    resp = client.get("/votacoes?categoria=ZIL-MIN")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "ZIL-MIN" in data[0]["categorias_zil"]


def test_campos_votacao_read(client, db_session):
    make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    db_session.commit()

    resp = client.get("/votacoes")
    item = resp.json()[0]
    for campo in ("id", "fonte_id", "data", "descricao", "resultado", "categorias_zil", "peso"):
        assert campo in item, f"Campo '{campo}' ausente"


def test_votacoes_sem_categoria_nao_aparecem(client, db_session):
    make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    make_votacao(db_session, categorias_zil=None)
    db_session.commit()

    resp = client.get("/votacoes")
    assert len(resp.json()) == 1


# ── GET /votacoes/{id}/votos ──

def test_votos_da_votacao(client, db_session):
    p1 = make_parlamentar(db_session, nome="Ana", partido="PT", uf="SP")
    p2 = make_parlamentar(db_session, nome="Bruno", partido="PL", uf="RJ")
    p3 = make_parlamentar(db_session, nome="Carla", partido="PSOL", uf="MG")
    v = make_votacao(db_session, categorias_zil=["ZIL-ENE"])
    make_voto(db_session, p1, v, VotoEnum.SIM)
    make_voto(db_session, p2, v, VotoEnum.NAO)
    make_voto(db_session, p3, v, VotoEnum.ABSTENCAO)
    db_session.commit()

    resp = client.get(f"/votacoes/{v.id}/votos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    nomes = {d["parlamentar_nome"] for d in data}
    assert nomes == {"Ana", "Bruno", "Carla"}


def test_campos_voto_read(client, db_session):
    p = make_parlamentar(db_session)
    v = make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    make_voto(db_session, p, v, VotoEnum.SIM)
    db_session.commit()

    resp = client.get(f"/votacoes/{v.id}/votos")
    item = resp.json()[0]
    for campo in ("parlamentar_id", "parlamentar_nome", "parlamentar_partido", "parlamentar_uf", "voto"):
        assert campo in item, f"Campo '{campo}' ausente"


def test_votacao_nao_encontrada(client):
    resp = client.get(f"/votacoes/{uuid.uuid4()}/votos")
    assert resp.status_code == 404


def test_parametro_invalido_retorna_422(client):
    # per_page = 0 viola ge=1
    resp = client.get("/votacoes?per_page=0")
    assert resp.status_code == 422


# ── GET /partidos/ranking ──

def test_ranking_partidos(client, db_session):
    make_parlamentar(db_session, partido="PT", score_zil=8.0)
    make_parlamentar(db_session, partido="PT", score_zil=6.0)
    make_parlamentar(db_session, partido="PL", score_zil=2.0)
    db_session.commit()

    resp = client.get("/parlamentares/partidos/ranking")
    assert resp.status_code == 200
    data = resp.json()
    pt = next(d for d in data if d["partido"] == "PT")
    assert pt["membros"] == 2
    assert pt["score_medio"] == 7.0
