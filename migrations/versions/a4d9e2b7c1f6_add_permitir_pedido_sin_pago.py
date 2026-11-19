"""add configuracion_landing.permitir_pedido_sin_pago

Change OpenSpec: add-interruptor-pedido-sin-pago

Revision ID: a4d9e2b7c1f6
Revises: f2c8a4e6b1d3
Create Date: 2026-11-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'a4d9e2b7c1f6'
down_revision = 'f2c8a4e6b1d3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('configuracion_landing', sa.Column('permitir_pedido_sin_pago', sa.Boolean(), nullable=False, server_default='true'))


def downgrade():
    op.drop_column('configuracion_landing', 'permitir_pedido_sin_pago')
