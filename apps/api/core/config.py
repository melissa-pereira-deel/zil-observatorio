"""Core configuration and database setup."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Root .env file, resolved relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://zil:zil@localhost:5432/zil"
    REDIS_URL: str = "redis://localhost:6379/0"
    TYPESENSE_HOST: str = "localhost"
    TYPESENSE_PORT: int = 8108
    TYPESENSE_API_KEY: str = "zil-dev-key"
    ENV: str = "development"
    CAMARA_API_BASE: str = "https://dadosabertos.camara.leg.br/api/v2"
    SENADO_API_BASE: str = "https://legis.senado.leg.br/dadosabertos"
    # Enrichment pipeline (Feature 002)
    ANTHROPIC_API_KEY: str = ""
    ADMIN_TOKEN: str = ""
    ENRICHMENT_MODEL: str = "claude-haiku-4-5-20251001"

    # extra="ignore": o .env é compartilhado com o docker compose e carrega
    # variáveis que são só dele (POSTGRES_USER, POSTGRES_PORT, ...). Sem isso,
    # qualquer variável não declarada aqui derruba a aplicação no import.
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")


settings = Settings()

# ── Production safety: require secrets to be set ──
if settings.ENV == "production":
    _missing = []
    if not settings.ANTHROPIC_API_KEY:
        _missing.append("ANTHROPIC_API_KEY")
    if not settings.ADMIN_TOKEN:
        _missing.append("ADMIN_TOKEN")
    if settings.DATABASE_URL.startswith("sqlite"):
        _missing.append("DATABASE_URL (must be PostgreSQL in production)")
    if _missing:
        raise RuntimeError(
            f"Production environment requires these variables: {', '.join(_missing)}. "
            f"Set them in your environment or .env file."
        )

engine = create_engine(settings.DATABASE_URL, echo=(settings.ENV == "development"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
