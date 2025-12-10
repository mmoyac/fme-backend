"""add_payment_fields

Revision ID: e7b39f4c3a21
Revises: df3f55fc1cf8
Create Date: 2025-12-09 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b39f4c3a21'
down_revision: Union[str, None] = 'df3f55fc1cf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar campos de Mercado Pago a la tabla pedidos
    op.add_column('pedidos', sa.Column('mp_preference_id', sa.String(), nullable=True))
    op.add_column('pedidos', sa.Column('mp_payment_id', sa.String(), nullable=True))
    op.add_column('pedidos', sa.Column('mp_status', sa.String(), nullable=True))
    op.add_column('pedidos', sa.Column('mp_external_reference', sa.String(), nullable=True))


def downgrade() -> None:
    # Eliminar campos de Mercado Pago
    op.drop_column('pedidos', 'mp_external_reference')
    op.drop_column('pedidos', 'mp_status')
    op.drop_column('pedidos', 'mp_payment_id')
    op.drop_column('pedidos', 'mp_preference_id')
