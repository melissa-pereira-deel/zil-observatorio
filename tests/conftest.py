"""Shared test fixtures for ZIL Observatório."""

import os
import sys
import uuid
from datetime import datetime
from typing import Generator
from pathlib import Path

# Order matters: repo root first (for apps.workers.*, packages.*),
# then apps/api (for core.config, models, main — matching internal imports).
REPO_ROOT = Path(__file__).parent.parent
API_DIR = REPO_ROOT / "apps" / "api"

for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Patch env before any app module is imported
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Use short-path imports that match what apps/api modules use internally.
# This ensures one single Base/MetaData instance across all imports.
from core.config import Base, get_db                         # noqa: E402
from models import (                                          # noqa: E402
    Parlamentar, Votacao, Voto, Proposicao, ScoreVotacao,
    FonteEnum, VotoEnum,
)
from main import app                                          # noqa: E402


# ── Engine + Session factory ──

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean database session per test."""
    Base.metadata.create_all(bind=_engine)
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with DB dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Seed helpers ──

def make_parlamentar(
    db: Session,
    nome: str = "João da Silva",
    partido: str = "PL",
    uf: str = "SP",
    score_zil: float | None = None,
    fonte_id: str | None = None,
) -> Parlamentar:
    p = Parlamentar(
        fonte_id=fonte_id or str(uuid.uuid4())[:8],
        fonte=FonteEnum.CAMARA,
        nome=nome,
        partido=partido,
        uf=uf,
        score_zil=score_zil,
        foto_url="https://example.com/foto.jpg",
    )
    db.add(p)
    db.flush()
    return p


def make_votacao(
    db: Session,
    descricao: str = "Votação de teste",
    categorias_zil: list[str] | None = None,
    direcao_esperada: str | None = "sim",
    peso: float = 1.0,
    fonte_id: str | None = None,
) -> Votacao:
    v = Votacao(
        fonte_id=fonte_id or str(uuid.uuid4())[:8],
        fonte=FonteEnum.CAMARA,
        data=datetime(2024, 6, 15, 14, 0, 0),
        descricao=descricao,
        resultado="aprovado",
        votos_sim=300,
        votos_nao=150,
        categorias_zil=categorias_zil,
        direcao_esperada=direcao_esperada,
        peso=peso,
    )
    db.add(v)
    db.flush()
    return v


def make_voto(
    db: Session,
    parlamentar: Parlamentar,
    votacao: Votacao,
    voto: VotoEnum = VotoEnum.SIM,
) -> Voto:
    v = Voto(
        votacao_id=votacao.id,
        parlamentar_id=parlamentar.id,
        voto=voto,
    )
    db.add(v)
    db.flush()
    return v


def make_proposicao(
    db: Session,
    tipo: str = "PL",
    numero: int = 1234,
    ano: int = 2024,
    ementa: str = "Regulamenta processamento de minerais estratégicos",
    categorias_zil: list[str] | None = None,
    fonte_id: str | None = None,
) -> Proposicao:
    p = Proposicao(
        fonte_id=fonte_id or str(uuid.uuid4())[:8],
        fonte=FonteEnum.CAMARA,
        tipo=tipo,
        numero=numero,
        ano=ano,
        ementa=ementa,
        categorias_zil=categorias_zil,
        relevancia_zil=0.85 if categorias_zil else None,
    )
    db.add(p)
    db.flush()
    return p
