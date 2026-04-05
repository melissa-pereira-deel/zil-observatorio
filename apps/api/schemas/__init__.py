"""Pydantic schemas for API request/response models."""

from datetime import datetime, date
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
    # Enrichment fields (Feature 002)
    contexto_status: Optional[str] = None
    resumo_simples: Optional[str] = None
    confianca: Optional[float] = None

    class Config:
        from_attributes = True


# ── Enrichment / Contexto (Feature 002) ──

class LeiReferenciadaRead(BaseModel):
    lei_id: str
    numero_artigo: str
    url_planalto: Optional[str] = None
    status: str
    texto_snippet: Optional[str] = None


class ProposicaoContexto(BaseModel):
    proposicao_id: UUID
    ementa_original: Optional[str] = None
    contexto_status: Optional[str] = None
    resumo_simples: Optional[str] = None
    glossario: Optional[dict] = None
    impacto_zil: Optional[str] = None
    leis_referenciadas: Optional[list[LeiReferenciadaRead]] = None
    confianca: Optional[float] = None
    enriquecido_em: Optional[datetime] = None
    versao_pipeline: str = "1.0"
    modelo_llm: Optional[str] = None
    fontes: list[str] = []

    model_config = ConfigDict(from_attributes=True)


# ── Votação ──

class ProposicaoSnippet(BaseModel):
    id: UUID
    tipo: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    ementa: Optional[str] = None
    resumo_simples: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


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
    proposicao: Optional[ProposicaoSnippet] = None

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
    proposicao_label: Optional[str] = None  # e.g. "PL 528/2020"
    proposicao_id: Optional[UUID] = None
    resumo_simples: Optional[str] = None  # AI-generated plain-language summary


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
