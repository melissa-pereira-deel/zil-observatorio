"""Core configuration and database setup."""

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://zil:zil@localhost:5432/zil"
    REDIS_URL: str = "redis://localhost:6379/0"
    TYPESENSE_HOST: str = "localhost"
    TYPESENSE_PORT: int = 8108
    TYPESENSE_API_KEY: str = "zil-dev-key"
    ENV: str = "development"
    CAMARA_API_BASE: str = "https://dadosabertos.camara.leg.br/api/v2"
    SENADO_API_BASE: str = "https://legis.senado.leg.br/dadosabertos"

    class Config:
        env_file = ".env"


settings = Settings()

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
