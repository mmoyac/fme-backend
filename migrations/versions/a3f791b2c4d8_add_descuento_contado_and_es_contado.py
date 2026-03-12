"""add descuento_contado to productos and es_contado to medios_pago

Revision ID: a3f791b2c4d8
Revises: 79f6c6112c15
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f791b2c4d8'
down_revision: Union[str, None] = '239399aa0903'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar descuento_contado a productos (% de descuento cuando el pago es al contado)
    op.add_column(
        'productos',
        sa.Column('descuento_contado', sa.Numeric(5, 2), nullable=True, server_default='0')
    )

    # Agregar es_contado a medios_pago (indica si este medio es "al contado")
    op.add_column(
        'medios_pago',
        sa.Column('es_contado', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('medios_pago', 'es_contado')
    op.drop_column('productos', 'descuento_contado')
