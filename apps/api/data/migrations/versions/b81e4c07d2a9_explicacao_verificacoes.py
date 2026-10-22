"""explicacoes: verificações de alegações e hash do contexto econômico

Revision ID: b81e4c07d2a9
Revises: 7f3c2e9a1b04
Create Date: 2026-10-21 23:00:00.000000

`verificacoes` guarda, por execução, cada alegação extraída e o que as
fontes catalogadas disseram sobre ela; `contexto_hash` identifica o pacote
de séries que as lentes leram. Ver apps/workers/explicacao/verificacao.py e
apps/workers/fontes/contexto.py. Colunas nulas: execuções da v1 não
verificam, e as anteriores a esta migration não têm contexto.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Ids de revisão do Alembic são hex por convenção, não segredo.
revision: str = 'b81e4c07d2a9'  # pragma: allowlist secret
down_revision: Union[str, None] = '7f3c2e9a1b04'  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('explicacoes') as batch:
        batch.add_column(sa.Column('verificacoes', sa.JSON(none_as_null=True), nullable=True))
        batch.add_column(sa.Column('contexto_hash', sa.String(length=16), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('explicacoes') as batch:
        batch.drop_column('contexto_hash')
        batch.drop_column('verificacoes')
