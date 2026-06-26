"""widen compras monetary columns to Numeric(12,2)

Amplía las columnas monetarias del flujo de compras de Numeric(10,2) a
Numeric(12,2) para evitar `numeric field overflow` en compras de monto alto (CLP).

Revision ID: f7a1c2d3e4b5
Revises: e5f6a7b8c9d0
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a1c2d3e4b5'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('compras', 'monto_total',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Numeric(12, 2),
                    existing_nullable=True)
    op.alter_column('detalles_compra', 'precio_unitario',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Numeric(12, 2),
                    existing_nullable=False)
    op.alter_column('productos', 'precio_compra',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Numeric(12, 2),
                    existing_nullable=True)


def downgrade() -> None:
    # Nota: el downgrade solo es seguro si no se registraron montos > 99.999.999,99.
    op.alter_column('productos', 'precio_compra',
                    existing_type=sa.Numeric(12, 2),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)
    op.alter_column('detalles_compra', 'precio_unitario',
                    existing_type=sa.Numeric(12, 2),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)
    op.alter_column('compras', 'monto_total',
                    existing_type=sa.Numeric(12, 2),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)
