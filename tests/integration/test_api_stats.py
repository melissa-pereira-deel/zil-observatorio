"""Integration tests for GET /stats (US-3)."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tests.conftest import make_parlamentar, make_votacao, make_proposicao
from models import IngestionRun


def _make_ingestion_run(db, status: str = "success", tipo: str = "full_sync", dt_offset_minutes: int = 0) -> IngestionRun:
    dt = datetime(2024, 3, 15, 14, 0, 0) + timedelta(minutes=dt_offset_minutes)
    run = IngestionRun(
        tipo=tipo,
        status=status,
        iniciado_em=dt,
        finalizado_em=dt + timedelta(minutes=30) if status != "running" else None,
        registros_processados=500,
        registros_criados=500,
        registros_atualizados=0,
        erros_count=0,
    )
    db.add(run)
    db.flush()
    return run


def test_stats_campos_obrigatorios(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()

    for campo in ("total_parlamentares", "total_deputados", "total_votacoes_zil", "score_medio", "ultima_atualizacao"):
        assert campo in data, f"Campo '{campo}' ausente em /stats"


def test_stats_sem_dados(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_parlamentares"] == 0
    assert data["total_deputados"] == 0
    assert data["score_medio"] is None
    assert data["ultima_atualizacao"] is None


def test_stats_sem_ingestion_run_ultima_atualizacao_nula(client, db_session):
    make_parlamentar(db_session, score_zil=5.0)
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    assert resp.json()["ultima_atualizacao"] is None


def test_stats_com_ingestion_run_success(client, db_session):
    _make_ingestion_run(db_session, status="success")
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ultima_atualizacao"] is not None


def test_stats_ignora_ingestion_run_failed(client, db_session):
    _make_ingestion_run(db_session, status="failed")
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    assert resp.json()["ultima_atualizacao"] is None


def test_stats_ignora_ingestion_run_running(client, db_session):
    _make_ingestion_run(db_session, status="running")
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    assert resp.json()["ultima_atualizacao"] is None


def test_stats_retorna_ultima_atualizacao_mais_recente(client, db_session):
    _make_ingestion_run(db_session, status="success", dt_offset_minutes=0)
    _make_ingestion_run(db_session, status="success", dt_offset_minutes=60)  # mais recente
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ultima_atualizacao"] is not None
    # Deve retornar o timestamp finalizado_em do mais recente (dt_offset_minutes=60)
    ts = datetime.fromisoformat(data["ultima_atualizacao"].replace("Z", "+00:00").replace("+00:00", ""))
    assert ts >= datetime(2024, 3, 15, 14, 30, 0)


def test_stats_contagens(client, db_session):
    make_parlamentar(db_session, score_zil=8.0)
    make_parlamentar(db_session, score_zil=4.0)
    make_votacao(db_session, categorias_zil=["ZIL-MIN"])
    make_votacao(db_session, categorias_zil=None)  # não conta
    make_proposicao(db_session, categorias_zil=["ZIL-FER"])
    db_session.commit()

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_parlamentares"] == 2
    assert data["total_deputados"] == 2
    assert data["total_votacoes_zil"] == 1
    assert data["score_medio"] == 6.0
