"""add cotizaciones, cotizacion_versiones, cotizacion_log y cotizacion_id en pedidos

Revision ID: e3f4a5b6c7d8
Revises: c1d2e3f4a5b6
Create Date: 2026-03-31 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------
    # 1. correlativo_cotizacion en tenants
    # --------------------------------------------------
    op.add_column('tenants', sa.Column('correlativo_cotizacion', sa.Integer(), nullable=False, server_default='0'))

    # --------------------------------------------------
    # 2. cotizacion_versiones (antes que cotizaciones por la FK circular)
    # --------------------------------------------------
    op.create_table(
        'cotizacion_versiones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cotizacion_id', sa.Integer(), nullable=False),          # FK se agrega después (circular)
        sa.Column('numero_version', sa.Integer(), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('monto_total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('motivo_cambio', sa.Text(), nullable=True),
        sa.Column('creado_por_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('es_version_aceptada', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cotizacion_versiones_id', 'cotizacion_versiones', ['id'])
    op.create_index('ix_cotizacion_versiones_cotizacion_id', 'cotizacion_versiones', ['cotizacion_id'])

    # --------------------------------------------------
    # 3. cotizaciones
    # --------------------------------------------------
    op.create_table(
        'cotizaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cliente_id', sa.Integer(), sa.ForeignKey('clientes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('canal_venta_id', sa.Integer(), sa.ForeignKey('canales_venta.id', ondelete='SET NULL'), nullable=True),
        sa.Column('numero_cotizacion', sa.String(50), nullable=False),
        sa.Column('estado_cotizacion_id', sa.Integer(), sa.ForeignKey('estados_cotizacion.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
        sa.Column('version_activa_id', sa.Integer(), sa.ForeignKey('cotizacion_versiones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_cotizacion', name='uq_cotizaciones_numero'),
    )
    op.create_index('ix_cotizaciones_id', 'cotizaciones', ['id'])
    op.create_index('ix_cotizaciones_tenant_id', 'cotizaciones', ['tenant_id'])
    op.create_index('ix_cotizaciones_numero_cotizacion', 'cotizaciones', ['numero_cotizacion'], unique=True)

    # --------------------------------------------------
    # 4. FK circular: cotizacion_versiones → cotizaciones
    # --------------------------------------------------
    op.create_foreign_key(
        'fk_cotizacion_versiones_cotizacion_id',
        'cotizacion_versiones', 'cotizaciones',
        ['cotizacion_id'], ['id'],
        ondelete='CASCADE'
    )

    # --------------------------------------------------
    # 5. cotizacion_log
    # --------------------------------------------------
    op.create_table(
        'cotizacion_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cotizacion_id', sa.Integer(), sa.ForeignKey('cotizaciones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_id', sa.Integer(), sa.ForeignKey('cotizacion_versiones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cotizacion_log_id', 'cotizacion_log', ['id'])
    op.create_index('ix_cotizacion_log_cotizacion_id', 'cotizacion_log', ['cotizacion_id'])

    # --------------------------------------------------
    # 6. cotizacion_id en pedidos
    # --------------------------------------------------
    op.add_column('pedidos', sa.Column('cotizacion_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_pedidos_cotizacion_id',
        'pedidos', 'cotizaciones',
        ['cotizacion_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_pedidos_cotizacion_id', 'pedidos', type_='foreignkey')
    op.drop_column('pedidos', 'cotizacion_id')

    op.drop_index('ix_cotizacion_log_cotizacion_id', table_name='cotizacion_log')
    op.drop_index('ix_cotizacion_log_id', table_name='cotizacion_log')
    op.drop_table('cotizacion_log')

    op.drop_constraint('fk_cotizacion_versiones_cotizacion_id', 'cotizacion_versiones', type_='foreignkey')

    op.drop_index('ix_cotizaciones_numero_cotizacion', table_name='cotizaciones')
    op.drop_index('ix_cotizaciones_tenant_id', table_name='cotizaciones')
    op.drop_index('ix_cotizaciones_id', table_name='cotizaciones')
    op.drop_table('cotizaciones')

    op.drop_index('ix_cotizacion_versiones_cotizacion_id', table_name='cotizacion_versiones')
    op.drop_index('ix_cotizacion_versiones_id', table_name='cotizacion_versiones')
    op.drop_table('cotizacion_versiones')

    op.drop_column('tenants', 'correlativo_cotizacion')
