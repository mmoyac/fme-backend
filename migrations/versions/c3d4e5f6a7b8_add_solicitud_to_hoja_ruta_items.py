"""add solicitud_id to hoja_ruta_items

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. pedido_id pasa a nullable
    op.alter_column('hoja_ruta_items', 'pedido_id', nullable=True)

    # 2. Agregar solicitud_id nullable
    op.add_column(
        'hoja_ruta_items',
        sa.Column(
            'solicitud_id',
            sa.Integer(),
            sa.ForeignKey('solicitudes_transferencia.solicitud_id', ondelete='RESTRICT'),
            nullable=True,
        )
    )

    # 3. Check: exactamente uno de los dos debe estar presente
    op.create_check_constraint(
        'ck_hoja_ruta_items_pedido_o_solicitud',
        'hoja_ruta_items',
        '(pedido_id IS NOT NULL AND solicitud_id IS NULL) OR (pedido_id IS NULL AND solicitud_id IS NOT NULL)'
    )


def downgrade():
    op.drop_constraint('ck_hoja_ruta_items_pedido_o_solicitud', 'hoja_ruta_items', type_='check')
    op.drop_column('hoja_ruta_items', 'solicitud_id')
    op.alter_column('hoja_ruta_items', 'pedido_id', nullable=False)
