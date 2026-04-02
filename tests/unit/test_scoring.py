"""Unit tests for the ZIL scoring engine."""

import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.scoring import calcular_alinhamento, recalcular_score_parlamentar
from models import Parlamentar, Votacao, Voto, ScoreVotacao, FonteEnum, VotoEnum


# ── calcular_alinhamento ──

def test_calcular_alinhamento_sim_esperado_sim():
    assert calcular_alinhamento(VotoEnum.SIM, "sim") == 1.0


def test_calcular_alinhamento_nao_esperado_nao():
    assert calcular_alinhamento(VotoEnum.NAO, "nao") == 1.0


def test_calcular_alinhamento_nao_esperado_sim():
    assert calcular_alinhamento(VotoEnum.NAO, "sim") == -1.0


def test_calcular_alinhamento_sim_esperado_nao():
    assert calcular_alinhamento(VotoEnum.SIM, "nao") == -1.0


def test_calcular_alinhamento_ausente():
    assert calcular_alinhamento(VotoEnum.AUSENTE, "sim") == 0.0


def test_calcular_alinhamento_abstencao():
    assert calcular_alinhamento(VotoEnum.ABSTENCAO, "sim") == 0.0


def test_calcular_alinhamento_obstrucao():
    assert calcular_alinhamento(VotoEnum.OBSTRUCAO, "sim") == 0.0


def test_calcular_alinhamento_artigo_17():
    assert calcular_alinhamento(VotoEnum.ARTIGO_17, "sim") == 0.0


# ── recalcular_score_parlamentar ──

def test_recalcular_score_sem_votos_zil(db_session):
    """Deputado sem votos em pautas ZIL retorna None."""
    p = _make_parlamentar(db_session)
    votacao = _make_votacao(db_session, categorias_zil=None, direcao_esperada=None)
    _make_voto(db_session, p, votacao, VotoEnum.SIM)
    db_session.commit()

    score = recalcular_score_parlamentar(db_session, p.id)
    assert score is None


def test_recalcular_score_sem_direcao_esperada(db_session):
    """Votação ZIL sem direção esperada não conta para o score."""
    p = _make_parlamentar(db_session)
    votacao = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada=None)
    _make_voto(db_session, p, votacao, VotoEnum.SIM)
    db_session.commit()

    score = recalcular_score_parlamentar(db_session, p.id)
    assert score is None


def test_recalcular_score_alinhamento_total(db_session):
    """Deputado que vota 100% alinhado → score +10.0."""
    p = _make_parlamentar(db_session)
    v1 = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim", peso=1.0)
    v2 = _make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="sim", peso=1.0)
    _make_voto(db_session, p, v1, VotoEnum.SIM)
    _make_voto(db_session, p, v2, VotoEnum.SIM)
    db_session.commit()

    score = recalcular_score_parlamentar(db_session, p.id)
    assert score == 10.0


def test_recalcular_score_contra_total(db_session):
    """Deputado que vota 100% contra → score -10.0."""
    p = _make_parlamentar(db_session)
    v1 = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim", peso=1.0)
    _make_voto(db_session, p, v1, VotoEnum.NAO)
    db_session.commit()

    score = recalcular_score_parlamentar(db_session, p.id)
    assert score == -10.0


def test_recalcular_score_misto(db_session):
    """1 voto alinhado + 1 contra → score 0.0."""
    p = _make_parlamentar(db_session)
    v1 = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim", peso=1.0)
    v2 = _make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="sim", peso=1.0)
    _make_voto(db_session, p, v1, VotoEnum.SIM)
    _make_voto(db_session, p, v2, VotoEnum.NAO)
    db_session.commit()

    score = recalcular_score_parlamentar(db_session, p.id)
    assert score == 0.0


def test_recalcular_score_com_pesos(db_session):
    """Peso 3x em votação positiva supera peso 1x negativa."""
    p = _make_parlamentar(db_session)
    v_pesado = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim", peso=3.0)
    v_leve = _make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="sim", peso=1.0)
    _make_voto(db_session, p, v_pesado, VotoEnum.SIM)   # +3
    _make_voto(db_session, p, v_leve, VotoEnum.NAO)     # -1
    db_session.commit()

    # (3 - 1) / (3 + 1) * 10 = 0.5 * 10 = 5.0
    score = recalcular_score_parlamentar(db_session, p.id)
    assert score == 5.0


def test_recalcular_score_ausente_nao_penaliza(db_session):
    """Ausência não penaliza — score é calculado só com votos ativos."""
    p = _make_parlamentar(db_session)
    v1 = _make_votacao(db_session, categorias_zil=["ZIL-MIN"], direcao_esperada="sim", peso=1.0)
    v2 = _make_votacao(db_session, categorias_zil=["ZIL-ENE"], direcao_esperada="sim", peso=1.0)
    _make_voto(db_session, p, v1, VotoEnum.SIM)
    _make_voto(db_session, p, v2, VotoEnum.AUSENTE)
    db_session.commit()

    # (+1 + 0) / (1 + 1) * 10 = 5.0
    score = recalcular_score_parlamentar(db_session, p.id)
    assert score == 5.0


# ── Helpers ──

def _make_parlamentar(db, nome: str = "Dep. Teste") -> Parlamentar:
    p = Parlamentar(
        fonte_id=str(uuid.uuid4())[:8],
        fonte=FonteEnum.CAMARA,
        nome=nome,
        partido="PT",
        uf="SP",
    )
    db.add(p)
    db.flush()
    return p


def _make_votacao(db, categorias_zil, direcao_esperada, peso=1.0) -> Votacao:
    v = Votacao(
        fonte_id=str(uuid.uuid4())[:8],
        fonte=FonteEnum.CAMARA,
        data=datetime(2024, 6, 1),
        descricao="Votação de teste",
        categorias_zil=categorias_zil,
        direcao_esperada=direcao_esperada,
        peso=peso,
    )
    db.add(v)
    db.flush()
    return v


def _make_voto(db, parlamentar: Parlamentar, votacao: Votacao, voto: VotoEnum) -> Voto:
    v = Voto(
        votacao_id=votacao.id,
        parlamentar_id=parlamentar.id,
        voto=voto,
    )
    db.add(v)
    db.flush()
    return v
