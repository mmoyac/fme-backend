"""add control manual de etiquetas impresas en ordenes_produccion

Change OpenSpec: add-control-etiquetas-op

Revision ID: e7b3d9a1c5f2
Revises: d5a1c7e3f9b2
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'e7b3d9a1c5f2'
down_revision = 'd5a1c7e3f9b2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ordenes_produccion', sa.Column('etiquetas_impresas_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ordenes_produccion', sa.Column('etiquetas_impresas_por_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_ordenes_produccion_etiquetas_impresas_por',
        'ordenes_produccion', 'users',
        ['etiquetas_impresas_por_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('fk_ordenes_produccion_etiquetas_impresas_por', 'ordenes_produccion', type_='foreignkey')
    op.drop_column('ordenes_produccion', 'etiquetas_impresas_por_id')
    op.drop_column('ordenes_produccion', 'etiquetas_impresas_at')
