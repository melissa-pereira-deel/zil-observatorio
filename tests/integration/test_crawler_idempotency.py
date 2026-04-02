"""Integration tests for crawler idempotency (SC-003)."""

import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import func, select
from models import Parlamentar, Votacao, Voto, FonteEnum, VotoEnum
from apps.workers.crawlers.camara import sync_deputados, sync_votacoes


# ── Helpers ──

def _fake_deputado(dep_id: int = 1001, partido: str = "PT", uf: str = "SP"):
    from packages.camara_client import DeputadoAPI
    return DeputadoAPI(
        id=dep_id,
        nome=f"Dep {dep_id}",
        siglaPartido=partido,
        siglaUf=uf,
        urlFoto=f"https://camara.leg.br/foto/{dep_id}.jpg",
        email=f"dep{dep_id}@camara.leg.br",
    )


def _fake_votacao(vot_id: str = "VOTID001"):
    from packages.camara_client import VotacaoAPI
    return VotacaoAPI(
        id=vot_id,
        data="2024-06-01T15:00:00",
        descricao="Votação sobre lítio e minerais estratégicos",
        aprovacao=True,
    )


def _fake_voto(dep_id: int = 1001, voto: str = "Sim"):
    from packages.camara_client import VotoAPI
    return VotoAPI(
        deputado_id=dep_id,
        deputado_nome=f"Dep {dep_id}",
        deputado_partido="PT",
        deputado_uf="SP",
        voto=voto,
    )


def _fake_votacao_detalhes(vot_id: str = "VOTID001"):
    return {
        "id": vot_id,
        "proposicaoPrincipal": None,
    }


# ── Tests ──

def test_sync_deputados_idempotente(db_session):
    """Re-executar sync_deputados não duplica parlamentares."""
    dep = _fake_deputado()

    with patch("apps.workers.crawlers.camara.CamaraClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.listar_deputados.return_value = [dep]
        mock_cls.return_value = mock_client

        sync_deputados(db_session)
        count_after_first = db_session.execute(select(func.count(Parlamentar.id))).scalar()

        sync_deputados(db_session)
        count_after_second = db_session.execute(select(func.count(Parlamentar.id))).scalar()

    assert count_after_first == count_after_second == 1


def test_sync_votacoes_idempotente(db_session):
    """Re-executar sync_votacoes não duplica votações nem votos."""
    dep = _fake_deputado()
    vot = _fake_votacao()
    voto = _fake_voto()
    detalhes = _fake_votacao_detalhes()

    with patch("apps.workers.crawlers.camara.CamaraClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.listar_deputados.return_value = [dep]
        mock_client.listar_votacoes.return_value = [vot]
        mock_client.obter_votos.return_value = [voto]
        mock_client.obter_votacao_detalhes.return_value = detalhes
        mock_client.obter_votacao_orientacoes.return_value = []
        mock_cls.return_value = mock_client

        sync_deputados(db_session)
        sync_votacoes(db_session, ano=2024)
        votos_after_first = db_session.execute(select(func.count(Voto.id))).scalar()
        votacoes_after_first = db_session.execute(select(func.count(Votacao.id))).scalar()

        sync_votacoes(db_session, ano=2024)
        votos_after_second = db_session.execute(select(func.count(Voto.id))).scalar()
        votacoes_after_second = db_session.execute(select(func.count(Votacao.id))).scalar()

    assert votacoes_after_first == votacoes_after_second == 1
    assert votos_after_first == votos_after_second == 1


def test_voto_stub_parlamentar_criado(db_session):
    """Voto de suplente (não na lista de deputados) cria parlamentar stub."""
    vot = _fake_votacao(vot_id="VOTID002")
    # suplente com id diferente dos deputados listados
    voto_suplente = _fake_voto(dep_id=9999, voto="Sim")
    detalhes = _fake_votacao_detalhes("VOTID002")

    with patch("apps.workers.crawlers.camara.CamaraClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.listar_deputados.return_value = []
        mock_client.listar_votacoes.return_value = [vot]
        mock_client.obter_votos.return_value = [voto_suplente]
        mock_client.obter_votacao_detalhes.return_value = detalhes
        mock_client.obter_votacao_orientacoes.return_value = []
        mock_cls.return_value = mock_client

        sync_deputados(db_session)
        sync_votacoes(db_session, ano=2024)

    stub = db_session.execute(
        select(Parlamentar).where(Parlamentar.fonte_id == "9999")
    ).scalar_one_or_none()

    assert stub is not None
    assert stub.nome == "Dep 9999"


def test_sync_deputados_atualiza_partido(db_session):
    """Deputado que mudou de partido é atualizado via upsert."""
    dep_v1 = _fake_deputado(dep_id=1001, partido="PT")
    dep_v2 = _fake_deputado(dep_id=1001, partido="PL")

    with patch("apps.workers.crawlers.camara.CamaraClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.listar_deputados.return_value = [dep_v1]
        mock_cls.return_value = mock_client
        sync_deputados(db_session)

        mock_client.listar_deputados.return_value = [dep_v2]
        sync_deputados(db_session)

    p = db_session.execute(
        select(Parlamentar).where(Parlamentar.fonte_id == "1001")
    ).scalar_one()
    assert p.partido == "PL"
    count = db_session.execute(select(func.count(Parlamentar.id))).scalar()
    assert count == 1
