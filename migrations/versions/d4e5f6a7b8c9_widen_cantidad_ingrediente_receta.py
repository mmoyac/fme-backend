"""widen ingredientes_receta.cantidad to Numeric(18,8)

La cantidad de un ingrediente se usa como FACTOR de costeo y requiere mas decimales
que los 3 actuales (Numeric(10,3)). Se amplia a Numeric(18,8) para preservar la
precision del factor sin truncar.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'ingredientes_receta',
        'cantidad',
        existing_type=sa.Numeric(10, 3),
        type_=sa.Numeric(18, 8),
        existing_nullable=False,
    )


def downgrade():
    # Posible perdida de decimales mas alla de 3.
    op.alter_column(
        'ingredientes_receta',
        'cantidad',
        existing_type=sa.Numeric(18, 8),
        type_=sa.Numeric(10, 3),
        existing_nullable=False,
    )
