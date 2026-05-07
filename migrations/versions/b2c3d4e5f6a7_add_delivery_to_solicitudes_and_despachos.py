"""add delivery to solicitudes and despachos

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Agregar requiere_delivery a solicitudes_transferencia
    op.add_column(
        'solicitudes_transferencia',
        sa.Column('requiere_delivery', sa.Boolean(), nullable=False, server_default='false')
    )

    # 2. Hacer pedido_id nullable en despachos
    op.alter_column('despachos', 'pedido_id', nullable=True)

    # 3. Eliminar unique constraint de pedido_id (solo aplica a pedidos, no solicitudes)
    op.drop_constraint('despachos_pedido_id_key', 'despachos', type_='unique')

    # 4. Agregar unique constraint condicional: pedido_id único cuando no es null
    op.create_index(
        'ix_despachos_pedido_id_unique',
        'despachos',
        ['pedido_id'],
        unique=True,
        postgresql_where=sa.text('pedido_id IS NOT NULL')
    )

    # 5. Agregar solicitud_id a despachos
    op.add_column(
        'despachos',
        sa.Column('solicitud_id', sa.Integer(), sa.ForeignKey('solicitudes_transferencia.solicitud_id', ondelete='CASCADE'), nullable=True)
    )

    # 6. Unique en solicitud_id cuando no es null
    op.create_index(
        'ix_despachos_solicitud_id_unique',
        'despachos',
        ['solicitud_id'],
        unique=True,
        postgresql_where=sa.text('solicitud_id IS NOT NULL')
    )

    # 7. Check constraint: exactamente uno de pedido_id o solicitud_id debe estar presente
    op.create_check_constraint(
        'ck_despachos_pedido_o_solicitud',
        'despachos',
        '(pedido_id IS NOT NULL AND solicitud_id IS NULL) OR (pedido_id IS NULL AND solicitud_id IS NOT NULL)'
    )


def downgrade():
    op.drop_constraint('ck_despachos_pedido_o_solicitud', 'despachos', type_='check')
    op.drop_index('ix_despachos_solicitud_id_unique', table_name='despachos')
    op.drop_column('despachos', 'solicitud_id')
    op.drop_index('ix_despachos_pedido_id_unique', table_name='despachos')
    op.create_unique_constraint('despachos_pedido_id_key', 'despachos', ['pedido_id'])
    op.alter_column('despachos', 'pedido_id', nullable=False)
    op.drop_column('solicitudes_transferencia', 'requiere_delivery')
