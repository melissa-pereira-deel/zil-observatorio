"""ZIL Observatório — API principal."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings, engine
from models import Base
from routers import parlamentares, legislativo, bussula


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev only). In production, use Alembic."""
    if settings.ENV == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ZIL Observatório API",
    description=(
        "API aberta para monitoramento do posicionamento de parlamentares "
        "brasileiros nas pautas de soberania industrial. "
        "Dados provenientes de fontes públicas oficiais."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://zilobservatorio.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parlamentares.router)
app.include_router(legislativo.router)
app.include_router(bussula.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "nome": "ZIL Observatório API",
        "versao": "0.1.0",
        "descricao": "Observability política para a soberania industrial do Brasil",
        "docs": "/docs",
        "manifesto": "https://zilobservatorio.org/manifesto",
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}
