"""proposicoes: statusProposicao completo e norma resultante

Revision ID: 3a9c5e71b2d4
Revises: b81e4c07d2a9
Create Date: 2026-11-05 12:00:00.000000

Até aqui `Proposicao` guardava só `situacao` (texto) e `ultimo_despacho`: o
discover buscava o detalhe na Câmara e jogava fora código da situação, órgão,
regime, apreciação, relator e proposição principal (docs/DISCOVERY-TRAMITACAO.md
§1.3, §5.1). Sem essas colunas não há onde gravar a última movimentação nem a lei
resultante, e o motor de fase fica sem entrada.

`status_bruto` é auditoria: o `statusProposicao` inteiro, como veio. As colunas
tipadas são o que o código lê.

Nada aqui é histórico. A situação de cada linha de `/tramitacoes` repete o valor
atual em vez do valor da época (disc. §3.2), então não existe coluna de situação
por linha: estas colunas dizem como a proposição está agora.

Todas nulas: esta migration só cria o lugar, e quem preenche são TRM-010 e
TRM-013. As colunas de norma entram aqui para manter a cadeia linear 011 → 026 →
027 (specs/013-tramitacao/spec.md §5.4).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Ids de revisão do Alembic são hex por convenção, não segredo.
revision: str = '3a9c5e71b2d4'  # pragma: allowlist secret
down_revision: Union[str, None] = 'b81e4c07d2a9'  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('proposicoes') as batch:
        batch.add_column(sa.Column('cod_situacao', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('sigla_orgao', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('orgao_fonte_id', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('orgao_nome', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('orgao_tipo_cod', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('cod_tipo_tramitacao', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('descricao_tramitacao', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('regime', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('apreciacao', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('status_sequencia', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('status_url', sa.String(length=500), nullable=True))
        batch.add_column(sa.Column('status_bruto', sa.JSON(none_as_null=True), nullable=True))
        batch.add_column(sa.Column('ultima_movimentacao_em', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('relator_fonte_id', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('relator_nome', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('principal_fonte_id', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('orgao_efetivo_sigla', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('orgao_efetivo_nome', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('detalhe_sincronizado_em', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('origem_registro', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('norma_tipo', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('norma_numero', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('norma_ano', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('norma_data', sa.Date(), nullable=True))
        batch.add_column(sa.Column('norma_veto', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('norma_fonte', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('norma_tramitacao_sequencia', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('norma_verificada_em', sa.DateTime(), nullable=True))

    op.create_index('ix_proposicao_ultima_mov', 'proposicoes', ['ultima_movimentacao_em'], unique=False)
    op.create_index('ix_proposicao_cod_situacao', 'proposicoes', ['cod_situacao'], unique=False)
    op.create_index('ix_proposicao_principal_fonte', 'proposicoes', ['principal_fonte_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_proposicao_principal_fonte', table_name='proposicoes')
    op.drop_index('ix_proposicao_cod_situacao', table_name='proposicoes')
    op.drop_index('ix_proposicao_ultima_mov', table_name='proposicoes')

    with op.batch_alter_table('proposicoes') as batch:
        batch.drop_column('norma_verificada_em')
        batch.drop_column('norma_tramitacao_sequencia')
        batch.drop_column('norma_fonte')
        batch.drop_column('norma_veto')
        batch.drop_column('norma_data')
        batch.drop_column('norma_ano')
        batch.drop_column('norma_numero')
        batch.drop_column('norma_tipo')
        batch.drop_column('origem_registro')
        batch.drop_column('detalhe_sincronizado_em')
        batch.drop_column('orgao_efetivo_nome')
        batch.drop_column('orgao_efetivo_sigla')
        batch.drop_column('principal_fonte_id')
        batch.drop_column('relator_nome')
        batch.drop_column('relator_fonte_id')
        batch.drop_column('ultima_movimentacao_em')
        batch.drop_column('status_bruto')
        batch.drop_column('status_url')
        batch.drop_column('status_sequencia')
        batch.drop_column('apreciacao')
        batch.drop_column('regime')
        batch.drop_column('descricao_tramitacao')
        batch.drop_column('cod_tipo_tramitacao')
        batch.drop_column('orgao_tipo_cod')
        batch.drop_column('orgao_nome')
        batch.drop_column('orgao_fonte_id')
        batch.drop_column('sigla_orgao')
        batch.drop_column('cod_situacao')
