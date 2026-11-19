"""add datos de etiqueta (origen, comuna, logo) en configuracion_landing

Change OpenSpec: add-formato-etiqueta-75x62 (fme-backoffice)

Revision ID: f2c8a4e6b1d3
Revises: e7b3d9a1c5f2
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'f2c8a4e6b1d3'
down_revision = 'e7b3d9a1c5f2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('configuracion_landing', sa.Column('etiqueta_origen', sa.String(100), nullable=True))
    op.add_column('configuracion_landing', sa.Column('etiqueta_comuna', sa.String(100), nullable=True))
    op.add_column('configuracion_landing', sa.Column('etiqueta_logo_url', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('configuracion_landing', 'etiqueta_logo_url')
    op.drop_column('configuracion_landing', 'etiqueta_comuna')
    op.drop_column('configuracion_landing', 'etiqueta_origen')
