"""add_local_cliente_id_to_items_pedido

Revision ID: a1f3c2d4e5b6
Revises: e79f998fb056
Create Date: 2026-03-06 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f3c2d4e5b6'
down_revision: Union[str, None] = 'e79f998fb056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna local_cliente_id a items_pedido
    op.add_column(
        'items_pedido',
        sa.Column('local_cliente_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_items_pedido_local_cliente',
        'items_pedido', 'locales_cliente',
        ['local_cliente_id'], ['id'],
        ondelete='SET NULL'
    )

    # Reemplazar constraint único antiguo por uno que incluye local_cliente_id
    op.drop_constraint('uix_item_pedido_producto_lote', 'items_pedido', type_='unique')
    op.create_unique_constraint(
        'uix_item_pedido_producto_lote_local',
        'items_pedido',
        ['pedido_id', 'producto_id', 'lote_id', 'local_cliente_id']
    )


def downgrade() -> None:
    op.drop_constraint('uix_item_pedido_producto_lote_local', 'items_pedido', type_='unique')
    op.create_unique_constraint(
        'uix_item_pedido_producto_lote',
        'items_pedido',
        ['pedido_id', 'producto_id', 'lote_id']
    )
    op.drop_constraint('fk_items_pedido_local_cliente', 'items_pedido', type_='foreignkey')
    op.drop_column('items_pedido', 'local_cliente_id')
