"""Integration tests for Feature 012 detail endpoints.

Tests T016, T023, T030, T031, T042, T050, T051, T060 — covering
situacao filters, enriched votacao fields, autores, parlamentar
proposicoes, temas, relacionadas, cadeia, and orgao/relator.
"""

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tests.conftest import make_parlamentar, make_proposicao, make_votacao
from models import (
    Proposicao, Votacao, Parlamentar, ProposicaoAutor, ProposicaoRelacao,
    FonteEnum,
)


# ── Helpers ──

def _make_proposicao_with_situacao(
    db, cod_situacao, regime=None, **kwargs
):
    """Create a proposicao with cod_situacao and categorias_zil set."""
    p = make_proposicao(db, categorias_zil=["ZIL-MIN"], **kwargs)
    p.cod_situacao = cod_situacao
    if regime:
        p.regime = regime
    db.flush()
    return p


# ── T016: Situacao filters ──

class TestT016SituacaoFilters:
    """GET /proposicoes?situacao_grupo= and ?regime= filters."""

    def test_filter_situacao_grupo_tramitando(self, client, db_session):
        """Only proposicoes with tramitando cod_situacao are returned."""
        p_tram = _make_proposicao_with_situacao(db_session, cod_situacao=903, numero=1)
        p_apro = _make_proposicao_with_situacao(db_session, cod_situacao=1140, numero=2)
        p_arq = _make_proposicao_with_situacao(db_session, cod_situacao=923, numero=3)
        db_session.commit()

        resp = client.get("/proposicoes?situacao_grupo=tramitando")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(p_tram.id)
        assert data[0]["situacao_grupo"] == "tramitando"

    def test_filter_situacao_grupo_aprovada(self, client, db_session):
        _make_proposicao_with_situacao(db_session, cod_situacao=903, numero=1)
        p_apro = _make_proposicao_with_situacao(db_session, cod_situacao=1140, numero=2)
        _make_proposicao_with_situacao(db_session, cod_situacao=923, numero=3)
        db_session.commit()

        resp = client.get("/proposicoes?situacao_grupo=aprovada")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(p_apro.id)
        assert data[0]["situacao_grupo"] == "aprovada"

    def test_filter_situacao_grupo_arquivada(self, client, db_session):
        _make_proposicao_with_situacao(db_session, cod_situacao=903, numero=1)
        _make_proposicao_with_situacao(db_session, cod_situacao=1140, numero=2)
        p_arq = _make_proposicao_with_situacao(db_session, cod_situacao=923, numero=3)
        db_session.commit()

        resp = client.get("/proposicoes?situacao_grupo=arquivada")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(p_arq.id)
        assert data[0]["situacao_grupo"] == "arquivada"

    def test_filter_regime_urgencia(self, client, db_session):
        p_urg = _make_proposicao_with_situacao(
            db_session, cod_situacao=903, regime="URGENCIA", numero=10,
        )
        _make_proposicao_with_situacao(
            db_session, cod_situacao=903, regime="ORDINARIO", numero=11,
        )
        db_session.commit()

        resp = client.get("/proposicoes?regime=URGENCIA")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(p_urg.id)
        assert data[0]["regime"] == "URGENCIA"

    def test_filter_situacao_grupo_invalid_returns_422(self, client, db_session):
        resp = client.get("/proposicoes?situacao_grupo=invalid")
        assert resp.status_code == 422


# ── T023: Votacao enriched fields ──

class TestT023VotacaoEnrichedFields:
    """GET /votacoes/{id} returns Feature 012 enriched fields."""

    def test_votacao_detail_returns_enriched_fields(self, client, db_session):
        v = make_votacao(db_session, categorias_zil=["ZIL-ENE"])
        v.aprovacao = 1
        v.sigla_orgao = "PLEN"
        v.proposicao_objeto = "Texto do substitutivo"
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/votacoes/{v.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["aprovacao"] == 1
        assert data["sigla_orgao"] == "PLEN"
        assert data["proposicao_objeto"] == "Texto do substitutivo"

    def test_votacao_detail_enriched_fields_null_when_absent(self, client, db_session):
        v = make_votacao(db_session, categorias_zil=["ZIL-MIN"])
        db_session.commit()

        resp = client.get(f"/votacoes/{v.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["aprovacao"] is None
        assert data["sigla_orgao"] is None
        assert data["proposicao_objeto"] is None


# ── T030: Autores endpoint ──

class TestT030AutoresEndpoint:
    """GET /proposicoes/{id}/autores returns AutorRead[] with ParlamentarSnippet."""

    def test_autores_with_parlamentar_link(self, client, db_session):
        parl = make_parlamentar(db_session, nome="Dep. Maria", partido="PT", uf="RJ")
        prop = make_proposicao(db_session, categorias_zil=["ZIL-FER"])

        autor = ProposicaoAutor(
            proposicao_id=prop.id,
            parlamentar_id=parl.id,
            nome="Dep. Maria",
            tipo="Deputado",
            ordem=1,
            proponente=True,
        )
        db_session.add(autor)
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/autores")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

        a = data[0]
        assert a["nome"] == "Dep. Maria"
        assert a["tipo"] == "Deputado"
        assert a["ordem"] == 1
        assert a["proponente"] is True

        # ParlamentarSnippet fields
        assert a["parlamentar"] is not None
        assert a["parlamentar"]["id"] == str(parl.id)
        assert a["parlamentar"]["nome"] == "Dep. Maria"
        assert a["parlamentar"]["partido"] == "PT"
        assert a["parlamentar"]["uf"] == "RJ"

    def test_autores_without_parlamentar_link(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-ENE"])

        autor = ProposicaoAutor(
            proposicao_id=prop.id,
            parlamentar_id=None,
            nome="Poder Executivo",
            tipo="Orgao",
            ordem=1,
            proponente=True,
        )
        db_session.add(autor)
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/autores")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["parlamentar"] is None
        assert data[0]["nome"] == "Poder Executivo"

    def test_autores_proposicao_not_found(self, client, db_session):
        resp = client.get(f"/proposicoes/{uuid.uuid4()}/autores")
        assert resp.status_code == 404

    def test_autores_multiple_ordered(self, client, db_session):
        parl1 = make_parlamentar(db_session, nome="Ana", partido="PT", uf="SP")
        parl2 = make_parlamentar(db_session, nome="Bruno", partido="PL", uf="RJ")
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])

        a1 = ProposicaoAutor(
            proposicao_id=prop.id,
            parlamentar_id=parl1.id,
            nome="Ana",
            tipo="Deputado",
            ordem=1,
            proponente=True,
        )
        a2 = ProposicaoAutor(
            proposicao_id=prop.id,
            parlamentar_id=parl2.id,
            nome="Bruno",
            tipo="Deputado",
            ordem=2,
            proponente=False,
        )
        db_session.add_all([a1, a2])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/autores")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["ordem"] == 1
        assert data[0]["nome"] == "Ana"
        assert data[1]["ordem"] == 2
        assert data[1]["nome"] == "Bruno"


# ── T031: Parlamentar proposicoes ──

class TestT031ParlamentarProposicoes:
    """GET /parlamentares/{id}/proposicoes returns authored proposicoes."""

    def test_parlamentar_proposicoes_via_autor_link(self, client, db_session):
        parl = make_parlamentar(db_session, nome="Carlos", partido="PSOL", uf="MG")
        prop = make_proposicao(
            db_session, tipo="PL", numero=999, ano=2025,
            categorias_zil=["ZIL-FER"],
        )

        autor = ProposicaoAutor(
            proposicao_id=prop.id,
            parlamentar_id=parl.id,
            nome="Carlos",
            tipo="Deputado",
            ordem=1,
            proponente=True,
        )
        db_session.add(autor)
        db_session.commit()

        resp = client.get(f"/parlamentares/{parl.id}/proposicoes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == str(prop.id)
        assert data[0]["tipo"] == "PL"
        assert data[0]["numero"] == 999

    def test_parlamentar_proposicoes_empty(self, client, db_session):
        parl = make_parlamentar(db_session, nome="Luisa", partido="MDB", uf="BA")
        db_session.commit()

        resp = client.get(f"/parlamentares/{parl.id}/proposicoes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_parlamentar_proposicoes_not_found(self, client, db_session):
        resp = client.get(f"/parlamentares/{uuid.uuid4()}/proposicoes")
        assert resp.status_code == 404


# ── T042: Temas endpoint ──

class TestT042TemasEndpoint:
    """GET /proposicoes/{id}/temas returns TemaRead[]."""

    def test_temas_with_data(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-ENE"])
        prop.temas_camara = [
            {"cod": 40, "tema": "Economia"},
            {"cod": 46, "tema": "Meio Ambiente"},
        ]
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/temas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["cod"] == 40
        assert data[0]["tema"] == "Economia"
        assert data[1]["cod"] == 46
        assert data[1]["tema"] == "Meio Ambiente"

    def test_temas_returns_empty_when_null(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])
        # temas_camara is None by default
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/temas")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_temas_proposicao_not_found(self, client, db_session):
        resp = client.get(f"/proposicoes/{uuid.uuid4()}/temas")
        assert resp.status_code == 404


# ── T050: Relacionadas endpoint ──

class TestT050RelacionadasEndpoint:
    """GET /proposicoes/{id}/relacionadas returns all related proposicoes."""

    def test_relacionadas_returns_all(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-FER"])

        rels = []
        for i, tipo in enumerate(["emenda", "substitutivo", "parecer"], start=1):
            r = ProposicaoRelacao(
                proposicao_id=prop.id,
                relacionada_fonte_id=str(1000 + i),
                tipo_relacao=tipo,
                sigla_tipo="EMC" if tipo == "emenda" else ("SBT" if tipo == "substitutivo" else "PAR"),
                numero=i,
                ano=2025,
                ementa=f"Relacao {tipo}",
            )
            rels.append(r)
        db_session.add_all(rels)
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/relacionadas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        tipos_retornados = {d["tipo_relacao"] for d in data}
        assert tipos_retornados == {"emenda", "substitutivo", "parecer"}

    def test_relacionadas_filter_tipo_relacao(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])

        r1 = ProposicaoRelacao(
            proposicao_id=prop.id,
            relacionada_fonte_id="2001",
            tipo_relacao="emenda",
            sigla_tipo="EMC",
            numero=1,
            ano=2024,
        )
        r2 = ProposicaoRelacao(
            proposicao_id=prop.id,
            relacionada_fonte_id="2002",
            tipo_relacao="parecer",
            sigla_tipo="PAR",
            numero=2,
            ano=2024,
        )
        db_session.add_all([r1, r2])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/relacionadas?tipo_relacao=emenda")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tipo_relacao"] == "emenda"

    def test_relacionadas_empty(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-ENE"])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/relacionadas")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_relacionadas_proposicao_not_found(self, client, db_session):
        resp = client.get(f"/proposicoes/{uuid.uuid4()}/relacionadas")
        assert resp.status_code == 404

    def test_relacionadas_invalid_tipo_relacao_returns_422(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-FER"])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}/relacionadas?tipo_relacao=invalido")
        assert resp.status_code == 422


# ── T051: Cadeia fields ──

class TestT051CadeiaFields:
    """GET /proposicoes/{id} includes cadeia object when prop_principal_id is set."""

    def test_cadeia_present_when_principal_id_set(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])
        prop.prop_principal_id = "12345"
        prop.prop_anterior_id = "12344"
        prop.prop_posterior_id = "12346"
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cadeia"] is not None
        assert data["cadeia"]["principal_fonte_id"] == "12345"
        assert data["cadeia"]["anterior_fonte_id"] == "12344"
        assert data["cadeia"]["posterior_fonte_id"] == "12346"

    def test_cadeia_null_when_no_chain_ids(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-ENE"])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cadeia"] is None

    def test_cadeia_partial_only_principal(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-FER"])
        prop.prop_principal_id = "99999"
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cadeia"] is not None
        assert data["cadeia"]["principal_fonte_id"] == "99999"
        assert data["cadeia"]["anterior_fonte_id"] is None
        assert data["cadeia"]["posterior_fonte_id"] is None


# ── T060: Orgao/relator ──

class TestT060OrgaoRelator:
    """GET /proposicoes/{id} returns orgao_situacao and relator snippet."""

    def test_orgao_situacao_returned(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])
        prop.orgao_situacao = "CCJC"
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgao_situacao"] == "CCJC"

    def test_relator_snippet_returned(self, client, db_session):
        relator = make_parlamentar(
            db_session, nome="Dep. Silva", partido="PP", uf="GO",
        )
        prop = make_proposicao(db_session, categorias_zil=["ZIL-ENE"])
        prop.relator_id = relator.id
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["relator"] is not None
        assert data["relator"]["id"] == str(relator.id)
        assert data["relator"]["nome"] == "Dep. Silva"
        assert data["relator"]["partido"] == "PP"
        assert data["relator"]["uf"] == "GO"

    def test_orgao_and_relator_null_when_absent(self, client, db_session):
        prop = make_proposicao(db_session, categorias_zil=["ZIL-FER"])
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgao_situacao"] is None
        assert data["relator"] is None

    def test_orgao_and_relator_together(self, client, db_session):
        relator = make_parlamentar(
            db_session, nome="Dep. Costa", partido="MDB", uf="RS",
        )
        prop = make_proposicao(db_session, categorias_zil=["ZIL-MIN"])
        prop.orgao_situacao = "CFT"
        prop.relator_id = relator.id
        db_session.flush()
        db_session.commit()

        resp = client.get(f"/proposicoes/{prop.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgao_situacao"] == "CFT"
        assert data["relator"]["id"] == str(relator.id)
        assert data["relator"]["nome"] == "Dep. Costa"
