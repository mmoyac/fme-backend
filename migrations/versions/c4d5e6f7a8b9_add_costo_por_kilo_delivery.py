"""add costo_por_kilo_delivery to configuracion_landing

Revision ID: c4d5e6f7a8b9
Revises: f7a1c2d3e4b5
Create Date: 2026-07-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d5e6f7a8b9'
down_revision = 'f7a1c2d3e4b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('configuracion_landing',
        sa.Column('costo_por_kilo_delivery', sa.Numeric(10, 2), nullable=True))


def downgrade():
    op.drop_column('configuracion_landing', 'costo_por_kilo_delivery')
