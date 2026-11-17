"""add modalidad de entrega al pedido

Change OpenSpec: add-modalidad-entrega-pedido

- pedidos: modalidad_entrega (RETIRO|DESPACHO), fecha_entrega, entregado_por_id,
  retirado_por_nombre, retirado_por_rut, nota_entrega.
- Backfill: DESPACHO si tiene costo_delivery, despacho o ítem de hoja de ruta; resto RETIRO.
  fecha_entrega desde hoja_ruta_items / despachos entregados.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'f5a6b7c8d9e0'
down_revision = 'e4f5a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pedidos', sa.Column('modalidad_entrega', sa.String(10), nullable=False, server_default='RETIRO'))
    op.add_column('pedidos', sa.Column('fecha_entrega', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pedidos', sa.Column('entregado_por_id', sa.Integer(),
                                       sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('pedidos', sa.Column('retirado_por_nombre', sa.String(120), nullable=True))
    op.add_column('pedidos', sa.Column('retirado_por_rut', sa.String(12), nullable=True))
    op.add_column('pedidos', sa.Column('nota_entrega', sa.Text(), nullable=True))

    op.execute("""
        UPDATE pedidos p SET modalidad_entrega = 'DESPACHO'
        WHERE p.costo_delivery IS NOT NULL
           OR EXISTS (SELECT 1 FROM despachos d WHERE d.pedido_id = p.id)
           OR EXISTS (SELECT 1 FROM hoja_ruta_items h WHERE h.pedido_id = p.id)
    """)
    # Fecha de entrega conocida: hoja de ruta, si no, despacho
    op.execute("""
        UPDATE pedidos p SET fecha_entrega = h.fecha_entrega
        FROM (SELECT pedido_id, max(fecha_entrega) fecha_entrega FROM hoja_ruta_items
              WHERE entregado AND fecha_entrega IS NOT NULL GROUP BY pedido_id) h
        WHERE h.pedido_id = p.id AND p.fecha_entrega IS NULL
    """)
    op.execute("""
        UPDATE pedidos p SET fecha_entrega = d.fecha_entrega
        FROM despachos d
        WHERE d.pedido_id = p.id AND d.fecha_entrega IS NOT NULL AND p.fecha_entrega IS NULL
    """)


def downgrade():
    for col in ('nota_entrega', 'retirado_por_rut', 'retirado_por_nombre',
                'entregado_por_id', 'fecha_entrega', 'modalidad_entrega'):
        op.drop_column('pedidos', col)
