"""agregar_unidad_compra_a_productos

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-03-23 13:00:00.000000

Agrega soporte para unidad de compra y factor de conversión en productos.
Permite que materias primas a granel se compren en una unidad (ej: saco)
y el sistema convierta automáticamente al inventario en otra unidad (ej: kg).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Descripción de la unidad de compra (ej: "Saco 25 kg", "Caja 12 un")
    op.add_column('productos',
        sa.Column('unidad_compra_descripcion', sa.String(100), nullable=True)
    )
    # Cuántas unidades de inventario equivale 1 unidad de compra (ej: 25 para saco de 25 kg)
    op.add_column('productos',
        sa.Column('factor_conversion_compra', sa.Numeric(10, 4), nullable=True, server_default='1')
    )


def downgrade() -> None:
    op.drop_column('productos', 'factor_conversion_compra')
    op.drop_column('productos', 'unidad_compra_descripcion')
