"""Integration tests for GET /parlamentares endpoints."""

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tests.conftest import make_parlamentar, make_votacao, make_voto
from models import VotoEnum


# ── GET /parlamentares ──

def test_listar_parlamentares_vazio(client):
    resp = client.get("/parlamentares")
    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_parlamentares_com_dados(client, db_session):
    make_parlamentar(db_session, nome="Ana Lima", uf="SP", score_zil=7.5)
    make_parlamentar(db_session, nome="Bruno Costa", uf="RJ", score_zil=3.2)
    make_parlamentar(db_session, nome="Carla Melo", uf="MG", score_zil=None)
    db_session.commit()

    resp = client.get("/parlamentares")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_filtro_por_uf(client, db_session):
    make_parlamentar(db_session, nome="Dep SP", uf="SP")
    make_parlamentar(db_session, nome="Dep GO", uf="GO")
    db_session.commit()

    resp = client.get("/parlamentares?uf=SP")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["uf"] == "SP"


def test_filtro_por_partido(client, db_session):
    make_parlamentar(db_session, nome="Dep PT", partido="PT")
    make_parlamentar(db_session, nome="Dep PL", partido="PL")
    db_session.commit()

    resp = client.get("/parlamentares?partido=PT")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["partido"] == "PT"


def test_ordenacao_score_desc(client, db_session):
    make_parlamentar(db_session, nome="Baixo", score_zil=2.0)
    make_parlamentar(db_session, nome="Alto", score_zil=9.0)
    make_parlamentar(db_session, nome="Sem score", score_zil=None)
    db_session.commit()

    resp = client.get("/parlamentares?ordem=score_desc")
    assert resp.status_code == 200
    data = resp.json()
    scores = [d["score_zil"] for d in data if d["score_zil"] is not None]
    assert scores == sorted(scores, reverse=True)


def test_campos_obrigatorios_ranking(client, db_session):
    make_parlamentar(db_session, score_zil=5.0)
    db_session.commit()

    resp = client.get("/parlamentares")
    assert resp.status_code == 200
    item = resp.json()[0]
    for campo in ("id", "nome", "partido", "uf", "fonte", "score_zil", "total_votos_zil"):
        assert campo in item, f"Campo '{campo}' ausente no response"


def test_paginacao(client, db_session):
    for i in range(5):
        make_parlamentar(db_session, nome=f"Dep {i}")
    db_session.commit()

    resp = client.get("/parlamentares?per_page=2&page=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_parametro_ordem_invalido(client):
    resp = client.get("/parlamentares?ordem=invalido")
    assert resp.status_code == 422


# ── GET /parlamentares/{id} ──

def test_obter_parlamentar(client, db_session):
    p = make_parlamentar(db_session, nome="Maria Sousa")
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}")
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Maria Sousa"


def test_obter_parlamentar_nao_encontrado(client):
    resp = client.get(f"/parlamentares/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── GET /parlamentares/{id}/votos-zil ──

def test_votos_zil_lista_vazia(client, db_session):
    p = make_parlamentar(db_session)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil")
    assert resp.status_code == 200
    assert resp.json() == []


def test_votos_zil_parlamentar(client, db_session):
    p = make_parlamentar(db_session)
    votacao = make_votacao(
        db_session,
        descricao="PL Lítio",
        categorias_zil=["ZIL-MIN"],
        direcao_esperada="sim",
    )
    make_voto(db_session, p, votacao, VotoEnum.SIM)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["alinhado"] is True
    assert "ZIL-MIN" in data[0]["categorias_zil"]


def test_votos_zil_nao_alinhado(client, db_session):
    p = make_parlamentar(db_session)
    votacao = make_votacao(db_session, categorias_zil=["ZIL-FER"], direcao_esperada="sim")
    make_voto(db_session, p, votacao, VotoEnum.NAO)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil")
    assert resp.status_code == 200
    assert resp.json()[0]["alinhado"] is False


def test_votos_zil_filtro_categoria(client, db_session):
    p = make_parlamentar(db_session)
    v_min = make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim")
    v_ene = make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="nao")
    make_voto(db_session, p, v_min, VotoEnum.SIM)
    make_voto(db_session, p, v_ene, VotoEnum.NAO)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil?categoria=ZIL-MIN")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "ZIL-MIN" in data[0]["categorias_zil"]


def test_votos_zil_sem_direcao_alinhado_nulo(client, db_session):
    p = make_parlamentar(db_session)
    votacao = make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada=None)
    make_voto(db_session, p, votacao, VotoEnum.SIM)
    db_session.commit()

    resp = client.get(f"/parlamentares/{p.id}/votos-zil")
    assert resp.status_code == 200
    assert resp.json()[0]["alinhado"] is None


def test_votos_zil_parlamentar_nao_encontrado(client):
    resp = client.get(f"/parlamentares/{uuid.uuid4()}/votos-zil")
    assert resp.status_code == 404
