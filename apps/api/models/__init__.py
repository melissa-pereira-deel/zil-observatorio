"""Database models for ZIL Observatório."""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, Numeric, Boolean, Date, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index, Enum as SAEnum, Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config import Base


# ── Enums ──

import enum

class FonteEnum(str, enum.Enum):
    CAMARA = "camara"
    SENADO = "senado"

class VotoEnum(str, enum.Enum):
    SIM = "sim"
    NAO = "nao"
    ABSTENCAO = "abstencao"
    AUSENTE = "ausente"
    OBSTRUCAO = "obstrucao"
    ARTIGO_17 = "artigo_17"

class TipoFinanciamento(str, enum.Enum):
    RECEITA = "receita"
    DESPESA = "despesa"

class TipoAlerta(str, enum.Enum):
    PROPOSICAO_NOVA = "proposicao_nova"
    VOTACAO = "votacao"
    TRAMITACAO = "tramitacao"
    SCORE_MUDOU = "score_mudou"

class CanalAlerta(str, enum.Enum):
    EMAIL = "email"
    PUSH = "push"
    TELEGRAM = "telegram"


# ── Models ──

class Parlamentar(Base):
    __tablename__ = "parlamentares"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fonte_id: Mapped[str] = mapped_column(String(50), nullable=False)
    fonte: Mapped[FonteEnum] = mapped_column(SAEnum(FonteEnum), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_civil: Mapped[Optional[str]] = mapped_column(String(255))
    partido: Mapped[Optional[str]] = mapped_column(String(50))
    uf: Mapped[Optional[str]] = mapped_column(String(2))
    foto_url: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    redes_sociais: Mapped[Optional[dict]] = mapped_column(JSON)
    mandato_inicio: Mapped[Optional[date]] = mapped_column(Date)
    mandato_fim: Mapped[Optional[date]] = mapped_column(Date)
    frentes_parlamentares: Mapped[Optional[list]] = mapped_column(JSON)
    score_zil: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    score_atualizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    votos: Mapped[list["Voto"]] = relationship(back_populates="parlamentar")
    scores_votacao: Mapped[list["ScoreVotacao"]] = relationship(back_populates="parlamentar")

    __table_args__ = (
        UniqueConstraint("fonte_id", "fonte", name="uq_parlamentar_fonte"),
        Index("ix_parlamentar_partido", "partido"),
        Index("ix_parlamentar_uf", "uf"),
        Index("ix_parlamentar_score", "score_zil"),
    )


class Proposicao(Base):
    __tablename__ = "proposicoes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fonte_id: Mapped[str] = mapped_column(String(50), nullable=False)
    fonte: Mapped[FonteEnum] = mapped_column(SAEnum(FonteEnum), nullable=False)
    tipo: Mapped[Optional[str]] = mapped_column(String(20))
    numero: Mapped[Optional[int]] = mapped_column(Integer)
    ano: Mapped[Optional[int]] = mapped_column(Integer)
    ementa: Mapped[Optional[str]] = mapped_column(Text)
    ementa_detalhada: Mapped[Optional[str]] = mapped_column(Text)
    autor_principal_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("parlamentares.id"))
    autores: Mapped[Optional[list]] = mapped_column(JSON)
    situacao: Mapped[Optional[str]] = mapped_column(String(255))
    data_apresentacao: Mapped[Optional[date]] = mapped_column(Date)
    ultimo_despacho: Mapped[Optional[str]] = mapped_column(Text)
    categorias_zil: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
    relevancia_zil: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    classificacao_automatica: Mapped[bool] = mapped_column(Boolean, default=True)
    url_inteiro_teor: Mapped[Optional[str]] = mapped_column(String(500))
    tramitacoes: Mapped[Optional[list]] = mapped_column(JSON)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Enrichment fields (Feature 002) ──
    contexto_status: Mapped[Optional[str]] = mapped_column(String(20))  # pendente|processando|pronto|falhou|llm_falhou
    resumo_simples: Mapped[Optional[str]] = mapped_column(Text)
    glossario: Mapped[Optional[dict]] = mapped_column(JSON)
    impacto_zil: Mapped[Optional[str]] = mapped_column(Text)
    leis_referenciadas: Mapped[Optional[list]] = mapped_column(JSON)
    confianca: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    ementa_hash: Mapped[Optional[str]] = mapped_column(String(64))
    enriquecido_em: Mapped[Optional[datetime]] = mapped_column(DateTime)

    votacoes: Mapped[list["Votacao"]] = relationship(back_populates="proposicao")
    explicacoes: Mapped[list["Explicacao"]] = relationship(back_populates="proposicao")

    __table_args__ = (
        UniqueConstraint("fonte_id", "fonte", name="uq_proposicao_fonte"),
        Index("ix_proposicao_tipo_ano", "tipo", "ano"),
        Index("ix_proposicao_contexto_status", "contexto_status"),
    )


class Votacao(Base):
    __tablename__ = "votacoes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fonte_id: Mapped[str] = mapped_column(String(50), nullable=False)
    fonte: Mapped[FonteEnum] = mapped_column(SAEnum(FonteEnum), nullable=False)
    proposicao_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("proposicoes.id"))
    data: Mapped[Optional[datetime]] = mapped_column(DateTime)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    resultado: Mapped[Optional[str]] = mapped_column(String(50))
    votos_sim: Mapped[Optional[int]] = mapped_column(Integer)
    votos_nao: Mapped[Optional[int]] = mapped_column(Integer)
    abstencoes: Mapped[Optional[int]] = mapped_column(Integer)
    categorias_zil: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
    direcao_esperada: Mapped[Optional[str]] = mapped_column(String(10))  # "sim" ou "nao"
    peso: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), default=1.0)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    proposicao: Mapped[Optional["Proposicao"]] = relationship(back_populates="votacoes")
    votos: Mapped[list["Voto"]] = relationship(back_populates="votacao")

    __table_args__ = (
        UniqueConstraint("fonte_id", "fonte", name="uq_votacao_fonte"),
        Index("ix_votacao_data", "data"),
    )


class Voto(Base):
    __tablename__ = "votos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    votacao_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("votacoes.id"), nullable=False)
    parlamentar_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("parlamentares.id"), nullable=False)
    voto: Mapped[VotoEnum] = mapped_column(SAEnum(VotoEnum), nullable=False)
    orientacao_partido: Mapped[Optional[str]] = mapped_column(String(20))
    orientacao_governo: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    votacao: Mapped["Votacao"] = relationship(back_populates="votos")
    parlamentar: Mapped["Parlamentar"] = relationship(back_populates="votos")

    __table_args__ = (
        UniqueConstraint("votacao_id", "parlamentar_id", name="uq_voto_votacao_parlamentar"),
    )


class ScoreVotacao(Base):
    __tablename__ = "scores_votacao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parlamentar_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("parlamentares.id"), nullable=False)
    votacao_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("votacoes.id"), nullable=False)
    categoria_zil: Mapped[str] = mapped_column(String(20), nullable=False)
    impacto: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)  # -1.0 a +1.0
    peso: Mapped[float] = mapped_column(Numeric(3, 1), default=1.0)
    justificativa: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parlamentar: Mapped["Parlamentar"] = relationship(back_populates="scores_votacao")

    __table_args__ = (
        UniqueConstraint("parlamentar_id", "votacao_id", name="uq_score_parlamentar_votacao"),
        Index("ix_score_parlamentar", "parlamentar_id"),
        Index("ix_score_categoria", "categoria_zil"),
    )


class IngestionRun(Base):
    """Log auditável de cada execução de ingestão (FR-009, FR-010)."""
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # deputados | votacoes | full_sync
    ano: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # running | success | failed | partial
    iniciado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    finalizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
    registros_processados: Mapped[int] = mapped_column(Integer, default=0)
    registros_criados: Mapped[int] = mapped_column(Integer, default=0)
    registros_atualizados: Mapped[int] = mapped_column(Integer, default=0)
    erros_count: Mapped[int] = mapped_column(Integer, default=0)
    erro_detalhes: Mapped[Optional[list]] = mapped_column(JSON)

    __table_args__ = (
        Index("ix_ingestion_tipo_status_dt", "tipo", "status", "iniciado_em"),
    )


class LeiArtigo(Base):
    """Cache de artigos de lei obtidos do Planalto.gov.br (Feature 002)."""
    __tablename__ = "lei_artigos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lei_id: Mapped[str] = mapped_column(String(50), nullable=False)        # e.g. "14744-2023", "lc-87-1996"
    numero_artigo: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "4", "3"
    texto_artigo: Mapped[Optional[str]] = mapped_column(Text)
    url_planalto: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="resolvido")
    obtido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("lei_id", "numero_artigo", name="uq_lei_artigo"),
        Index("ix_lei_artigo_lei_id", "lei_id"),
        Index("ix_lei_artigo_expira_em", "expira_em"),
    )


class Financiamento(Base):
    __tablename__ = "financiamentos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parlamentar_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("parlamentares.id"))
    eleicao_ano: Mapped[Optional[int]] = mapped_column(Integer)
    tipo: Mapped[TipoFinanciamento] = mapped_column(SAEnum(TipoFinanciamento))
    doador_nome: Mapped[Optional[str]] = mapped_column(String(500))
    doador_cnpj_cpf: Mapped[Optional[str]] = mapped_column(String(20))
    doador_setor: Mapped[Optional[str]] = mapped_column(String(255))
    valor: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    data: Mapped[Optional[date]] = mapped_column(Date)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_financiamento_parlamentar", "parlamentar_id"),
        Index("ix_financiamento_doador", "doador_cnpj_cpf"),
    )


# ── Explicação de proposição (pipeline de agentes) ──

class Explicacao(Base):
    """Uma execução do pipeline de explicação sobre uma proposição.

    Versionada por execução, de propósito: várias linhas por proposição
    coexistem, uma por `pipeline_versao` (hash do YAML do pipeline) e por
    `texto_hash` (o inteiro teor que foi lido). É o que permite rodar duas
    abordagens sobre o mesmo conjunto e comparar lado a lado — e é o que a
    tabela `proposicoes` não permitiria com colunas, onde a execução nova
    sobrescreveria a anterior.
    """

    __tablename__ = "explicacoes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposicao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("proposicoes.id"), nullable=False
    )
    pipeline_versao: Mapped[str] = mapped_column(String(16), nullable=False)
    texto_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # As três saídas. Nulas quando status != pronto.
    resumo_didatico: Mapped[Optional[str]] = mapped_column(Text)
    resumo_detalhado: Mapped[Optional[str]] = mapped_column(Text)
    analise_sistemica: Mapped[Optional[dict]] = mapped_column(JSON(none_as_null=True))

    # Evidência: afirmações por lente (com citações) e dissensos. É o que
    # torna a explicação auditável sem o modelo (RFC-006 §7).
    evidencias: Mapped[Optional[dict]] = mapped_column(JSON(none_as_null=True))

    # Uma entrada por alegação extraída e conferida contra o catálogo de
    # fontes (só variantes com verificador). Veredito por número, nunca selo
    # da explicação.
    verificacoes: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
    # Hash do contexto econômico pré-registrado que as lentes leram
    # (apps/workers/fontes/contexto.py). Mesmo hash = mesmos números.
    contexto_hash: Mapped[Optional[str]] = mapped_column(String(16))

    # Reprodutibilidade: modelos, hashes de instruções e versões por agente.
    meta: Mapped[Optional[dict]] = mapped_column(JSON(none_as_null=True))
    metricas: Mapped[Optional[dict]] = mapped_column(JSON(none_as_null=True))
    problemas: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))

    status: Mapped[str] = mapped_column(String(24), nullable=False)  # pronto|invalido|lentes_indisponiveis
    custo_estimado: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    proposicao: Mapped["Proposicao"] = relationship(back_populates="explicacoes")

    __table_args__ = (
        UniqueConstraint("proposicao_id", "pipeline_versao", "texto_hash", name="uq_explicacao_execucao"),
        Index("ix_explicacao_proposicao_versao", "proposicao_id", "pipeline_versao"),
        Index("ix_explicacao_status", "status"),
    )
