"""Recusa do modelo gravada como resumo: a API não publica, e o script re-marca."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tests.conftest import make_proposicao, make_votacao
from scripts.marcar_recusas import marcar_recusas

RECUSA = "Não tenho informações suficientes para explicar esta proposição. O contexto fornecido apenas menciona o Paten."
RESUMO = "Cria um programa para financiar projetos de energia limpa."


def _enriquecida(db, numero, resumo, status="pronto"):
    p = make_proposicao(db, numero=numero, categorias_zil=["ZIL-ENE"])
    p.contexto_status = status
    p.resumo_simples = resumo
    p.glossario = {"Paten": "Sigla do programa"}
    p.impacto_zil = "Não posso avaliar o impacto."
    db.flush()
    return p


def test_script_remarca_so_as_recusas(db_session):
    recusa = _enriquecida(db_session, 327, RECUSA)
    boa = _enriquecida(db_session, 1, RESUMO)

    assert [p.numero for p in marcar_recusas(db_session, dry_run=True)] == [327]
    assert recusa.contexto_status == "pronto"  # dry-run não grava

    marcar_recusas(db_session)
    assert recusa.contexto_status == "llm_recusou"
    assert recusa.resumo_simples == RECUSA  # texto fica para auditoria
    assert boa.contexto_status == "pronto"
    assert marcar_recusas(db_session) == []  # idempotente


def test_api_nao_publica_resumo_de_recusa(client, db_session):
    p = _enriquecida(db_session, 327, RECUSA, status="llm_recusou")
    v = make_votacao(db_session)
    v.proposicao_id = p.id
    db_session.commit()

    assert client.get("/proposicoes").json()[0]["resumo_simples"] is None
    assert client.get(f"/proposicoes/{p.id}").json()["resumo_simples"] is None
    ctx = client.get(f"/proposicoes/{p.id}/contexto").json()
    assert ctx["contexto_status"] == "llm_recusou"
    assert ctx["resumo_simples"] is None and ctx["glossario"] is None and ctx["impacto_zil"] is None
    assert client.get(f"/votacoes/{v.id}").json()["proposicao"]["resumo_simples"] is None


def test_api_publica_resumo_pronto(client, db_session):
    p = _enriquecida(db_session, 1, RESUMO)
    db_session.commit()
    assert client.get(f"/proposicoes/{p.id}").json()["resumo_simples"] == RESUMO
    assert client.get(f"/proposicoes/{p.id}/contexto").json()["glossario"] == {"Paten": "Sigla do programa"}


def test_recusa_conta_como_sem_analise(client, db_session):
    _enriquecida(db_session, 327, RECUSA, status="llm_recusou")
    db_session.commit()
    assert [p["numero"] for p in client.get("/proposicoes?analise=pendente").json()] == [327]
