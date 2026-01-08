"""add_access_logs_table

Revision ID: 057e7850dce2
Revises: 454134e50340
Create Date: 2026-01-08 15:34:44.874058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '057e7850dce2'
down_revision: Union[str, None] = '454134e50340'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar tabela access_logs
    op.create_table('access_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('log_type', sa.String(length=50), nullable=False),
    sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Nota: Não alteramos o tipo da coluna role, pois o UserRoleType funciona
    # como String no banco e o mapeamento é feito pela aplicação


def downgrade() -> None:
    op.drop_table('access_logs')
