"""Pydantic schemas for API request/response models."""

from datetime import datetime, date
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


# ── Parlamentar ──

class ParlamentarBase(BaseModel):
    nome: str
    partido: Optional[str] = None
    uf: Optional[str] = None
    fonte: str
    foto_url: Optional[str] = None

class ParlamentarRead(ParlamentarBase):
    id: UUID
    fonte_id: str
    nome_civil: Optional[str] = None
    email: Optional[str] = None
    redes_sociais: Optional[dict] = None
    frentes_parlamentares: Optional[list] = None
    score_zil: Optional[float] = None
    score_atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

class ParlamentarRanking(BaseModel):
    id: UUID
    nome: str
    partido: Optional[str] = None
    uf: Optional[str] = None
    foto_url: Optional[str] = None
    fonte: str
    score_zil: Optional[float] = None
    total_votos_zil: int = 0

    class Config:
        from_attributes = True


# ── Proposição ──

class ProposicaoRead(BaseModel):
    id: UUID
    fonte_id: str
    fonte: str
    tipo: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    ementa: Optional[str] = None
    situacao: Optional[str] = None
    data_apresentacao: Optional[date] = None
    categorias_zil: Optional[list[str]] = None
    relevancia_zil: Optional[float] = None
    url_inteiro_teor: Optional[str] = None

    class Config:
        from_attributes = True


# ── Votação ──

class VotacaoRead(BaseModel):
    id: UUID
    fonte_id: str
    fonte: str
    data: Optional[datetime] = None
    descricao: Optional[str] = None
    resultado: Optional[str] = None
    votos_sim: Optional[int] = None
    votos_nao: Optional[int] = None
    categorias_zil: Optional[list[str]] = None
    direcao_esperada: Optional[str] = None
    peso: Optional[float] = None

    class Config:
        from_attributes = True


# ── Voto Individual ──

class VotoRead(BaseModel):
    parlamentar_id: UUID
    parlamentar_nome: str
    parlamentar_partido: Optional[str] = None
    parlamentar_uf: Optional[str] = None
    voto: str
    orientacao_partido: Optional[str] = None

    class Config:
        from_attributes = True


# ── Histórico de Votos do Parlamentar em Pautas ZIL ──

class VotoHistorico(BaseModel):
    votacao_id: UUID
    data: Optional[datetime] = None
    descricao: Optional[str] = None
    categorias_zil: Optional[list[str]] = None
    voto: str
    direcao_esperada: Optional[str] = None
    alinhado: Optional[bool] = None


# ── Stats ──

class StatsGeral(BaseModel):
    total_parlamentares: int
    total_deputados: int
    total_senadores: int
    total_proposicoes_zil: int
    total_votacoes_zil: int
    score_medio: Optional[float] = None
    ultima_atualizacao: Optional[datetime] = None


# ── Paginação ──

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
