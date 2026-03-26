"""add token_seguimiento to pedidos

Revision ID: a1b2c3d4e5f6
Revises: ff911497bb86
Create Date: 2026-03-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = '38d95567fc0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pedidos', sa.Column('token_seguimiento', sa.String(64), nullable=True))
    op.create_unique_constraint('uq_pedidos_token_seguimiento', 'pedidos', ['token_seguimiento'])
    op.create_index('ix_pedidos_token_seguimiento', 'pedidos', ['token_seguimiento'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_pedidos_token_seguimiento', table_name='pedidos')
    op.drop_constraint('uq_pedidos_token_seguimiento', 'pedidos', type_='unique')
    op.drop_column('pedidos', 'token_seguimiento')
