"""add costo_promedio a productos

Change OpenSpec: add-valorizacion-inventario

- productos.costo_promedio: costo promedio ponderado neto por unidad de inventario,
  global por producto. Backfill con COALESCE(precio_compra / factor_conversion_compra, costo_fabricacion).

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'e4f5a6b7c8d9'
down_revision = 'd3e4f5a6b7c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('productos', sa.Column('costo_promedio', sa.Numeric(12, 4), nullable=True))
    # precio_compra es por UNIDAD DE COMPRA (ej. saco); costo_promedio es por unidad de inventario (ej. kg)
    op.execute("""
        UPDATE productos
        SET costo_promedio = COALESCE(
            precio_compra / NULLIF(COALESCE(factor_conversion_compra, 1), 0),
            costo_fabricacion
        )
    """)


def downgrade():
    op.drop_column('productos', 'costo_promedio')
