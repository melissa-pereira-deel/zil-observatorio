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


# ── POST /proposicoes/{id}/enriquecer — autenticação por header ──
#
# O token trafega em `Authorization: Bearer <ADMIN_TOKEN>`, nunca em query
# string: URLs vazam em log de servidor, histórico de browser e header Referer.

@pytest.fixture
def admin_token(monkeypatch):
    """Configura um ADMIN_TOKEN conhecido para os testes de autenticação."""
    from core.config import settings

    monkeypatch.setattr(settings, "ADMIN_TOKEN", "token-de-teste-123")
    return "token-de-teste-123"


def test_enriquecer_sem_header_retorna_401(client, db_session, admin_token):
    p = make_proposicao(db_session)
    resp = client.post(f"/proposicoes/{p.id}/enriquecer")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"


def test_enriquecer_com_token_errado_retorna_401(client, db_session, admin_token):
    p = make_proposicao(db_session)
    resp = client.post(
        f"/proposicoes/{p.id}/enriquecer",
        headers={"Authorization": "Bearer token-errado"},
    )
    assert resp.status_code == 401


def test_enriquecer_com_esquema_errado_retorna_401(client, db_session, admin_token):
    """Basic em vez de Bearer não passa, mesmo com o token correto."""
    p = make_proposicao(db_session)
    resp = client.post(
        f"/proposicoes/{p.id}/enriquecer",
        headers={"Authorization": f"Basic {admin_token}"},
    )
    assert resp.status_code == 401


def test_enriquecer_por_query_string_nao_autentica(client, db_session, admin_token):
    """O contrato antigo (token na URL) foi removido — não deve mais funcionar."""
    p = make_proposicao(db_session)
    resp = client.post(f"/proposicoes/{p.id}/enriquecer?admin_token={admin_token}")
    assert resp.status_code == 401


def test_enriquecer_sem_admin_token_configurado_retorna_503(client, db_session, monkeypatch):
    """Servidor sem ADMIN_TOKEN não deve aceitar token vazio como válido."""
    from core.config import settings

    monkeypatch.setattr(settings, "ADMIN_TOKEN", "")
    p = make_proposicao(db_session)
    resp = client.post(
        f"/proposicoes/{p.id}/enriquecer",
        headers={"Authorization": "Bearer "},
    )
    assert resp.status_code == 503


def test_enriquecer_com_token_valido_passa_da_autenticacao(client, db_session, admin_token):
    """Token válido autentica; proposição inexistente responde 404, não 401."""
    resp = client.post(
        f"/proposicoes/{uuid.uuid4()}/enriquecer",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404
