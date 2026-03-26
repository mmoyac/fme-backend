"""add max_km_delivery to configuracion_landing

Revision ID: d1e2f3a4b5c6
Revises: c3d1e8f2a7b9
Create Date: 2026-03-25 10:00:00.000000

Agrega:
- Campo max_km_delivery en configuracion_landing: distancia máxima en km para aceptar delivery
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'dbd9fc2192b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'configuracion_landing',
        sa.Column('max_km_delivery', sa.Numeric(6, 2), nullable=True,
                  comment='Distancia máxima en kilómetros para aceptar pedidos con delivery. NULL = sin límite.')
    )


def downgrade() -> None:
    op.drop_column('configuracion_landing', 'max_km_delivery')
