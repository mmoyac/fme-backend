"""add afecta_inventario to tipos_producto

Permite distinguir tipos de producto que afectan inventario (insumos fisicos) de los
operacionales (arriendo, electricidad, HH produccion, etc.), que se costean pero no
manejan stock. Aditiva: default true. El cliente marca los tipos operacionales
(p. ej. SERVICIO) como afecta_inventario=false desde el mantenedor.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-23 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'tipos_producto',
        sa.Column(
            'afecta_inventario',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade():
    op.drop_column('tipos_producto', 'afecta_inventario')
