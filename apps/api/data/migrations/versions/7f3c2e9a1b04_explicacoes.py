"""explicacoes — execuções versionadas do pipeline de explicação

Revision ID: 7f3c2e9a1b04
Revises: 6d2a71d15687
Create Date: 2026-10-21 18:00:00.000000

Uma linha por (proposição, versão do pipeline, hash do texto lido). Várias
execuções por proposição coexistem de propósito: é o que permite comparar
abordagens lado a lado. Ver apps/api/models/__init__.py::Explicacao.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Ids de revisão do Alembic são hex por convenção, não segredo — o detect-secrets
# os lê como 'Hex High Entropy String'.
revision: str = '7f3c2e9a1b04'  # pragma: allowlist secret
down_revision: Union[str, None] = '6d2a71d15687'  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'explicacoes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('proposicao_id', sa.Uuid(), nullable=False),
        sa.Column('pipeline_versao', sa.String(length=16), nullable=False),
        sa.Column('texto_hash', sa.String(length=64), nullable=False),
        sa.Column('resumo_didatico', sa.Text(), nullable=True),
        sa.Column('resumo_detalhado', sa.Text(), nullable=True),
        sa.Column('analise_sistemica', sa.JSON(none_as_null=True), nullable=True),
        sa.Column('evidencias', sa.JSON(none_as_null=True), nullable=True),
        sa.Column('meta', sa.JSON(none_as_null=True), nullable=True),
        sa.Column('metricas', sa.JSON(none_as_null=True), nullable=True),
        sa.Column('problemas', sa.JSON(none_as_null=True), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('custo_estimado', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['proposicao_id'], ['proposicoes.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('proposicao_id', 'pipeline_versao', 'texto_hash', name='uq_explicacao_execucao'),
    )
    op.create_index('ix_explicacao_proposicao_versao', 'explicacoes', ['proposicao_id', 'pipeline_versao'], unique=False)
    op.create_index('ix_explicacao_status', 'explicacoes', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_explicacao_status', table_name='explicacoes')
    op.drop_index('ix_explicacao_proposicao_versao', table_name='explicacoes')
    op.drop_table('explicacoes')
