"""inventario_cantidad_decimal_granel

Revision ID: c1a2b3d4e5f6
Revises: f4e2d1c8b9a7
Create Date: 2026-03-23 12:00:00.000000

Permite cantidades decimales en inventario para soportar productos a granel
(ej: harina medida en kg, almendras vendidas en bolsitas de 100g compradas en bolsas de 25kg).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = 'f4e2d1c8b9a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # inventario.cantidad_stock
    op.alter_column('inventario', 'cantidad_stock',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=False,
                    existing_server_default='0')

    # movimientos_inventario.cantidad
    op.alter_column('movimientos_inventario', 'cantidad',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=False)

    # productos.stock_minimo y stock_critico
    op.alter_column('productos', 'stock_minimo',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True,
                    existing_server_default='0')

    op.alter_column('productos', 'stock_critico',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True,
                    existing_server_default='0')

    # items_solicitud_transferencia: cantidades de transferencias entre locales
    op.alter_column('items_solicitud_transferencia', 'cantidad_solicitada',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=False)

    op.alter_column('items_solicitud_transferencia', 'cantidad_aprobada',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True)

    op.alter_column('items_solicitud_transferencia', 'cantidad_recibida',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True)

    # picking_items: cantidades del proceso de picking/despacho
    op.alter_column('picking_items', 'cantidad_solicitada',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True)

    op.alter_column('picking_items', 'cantidad_pickeada',
                    existing_type=sa.Integer(),
                    type_=sa.Numeric(10, 3),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('picking_items', 'cantidad_pickeada',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True)

    op.alter_column('picking_items', 'cantidad_solicitada',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True)

    op.alter_column('items_solicitud_transferencia', 'cantidad_recibida',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True)

    op.alter_column('items_solicitud_transferencia', 'cantidad_aprobada',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True)

    op.alter_column('items_solicitud_transferencia', 'cantidad_solicitada',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=False)

    op.alter_column('productos', 'stock_critico',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True,
                    existing_server_default='0')

    op.alter_column('productos', 'stock_minimo',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=True,
                    existing_server_default='0')

    op.alter_column('movimientos_inventario', 'cantidad',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=False)

    op.alter_column('inventario', 'cantidad_stock',
                    existing_type=sa.Numeric(10, 3),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    existing_server_default='0')
