"""add peso_bruto to productos

Revision ID: b1c4d7e2f3a5
Revises: a8b3c9d2e1f4
Create Date: 2026-03-13 15:45:00.000000

Agrega campo peso_bruto (kg) a la tabla productos.
Se usa para calcular la carga total por vehículo en delivery.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c4d7e2f3a5'
down_revision: Union[str, None] = 'a8b3c9d2e1f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'productos',
        sa.Column('peso_bruto', sa.Numeric(8, 3), nullable=True,
                  comment='Peso bruto en kg (producto + empaque). Usado para asignación de vehículos en delivery.')
    )


def downgrade() -> None:
    op.drop_column('productos', 'peso_bruto')
