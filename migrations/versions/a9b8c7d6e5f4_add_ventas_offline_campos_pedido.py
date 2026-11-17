"""add campos ventas offline / idempotencia a pedidos

Change OpenSpec: add-ventas-offline-backoffice (Fase 1)

- client_uuid: clave de idempotencia generada por el cliente (POS backoffice).
  Índice único (tenant_id, client_uuid); en PostgreSQL los NULL no colisionan,
  así que los pedidos sin client_uuid (landing, integraciones) no se ven afectados.
- fecha_venta_cliente, origen, turno_caja_id, numero_provisorio, diferencia_precio:
  soporte para ventas registradas sin conexión y sincronizadas después.

Revision ID: a9b8c7d6e5f4
Revises: c4d5e6f7a8b9
Create Date: 2026-11-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'a9b8c7d6e5f4'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pedidos', sa.Column('client_uuid', sa.String(36), nullable=True))
    op.add_column('pedidos', sa.Column('fecha_venta_cliente', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pedidos', sa.Column('origen', sa.String(10), nullable=False, server_default='ONLINE'))
    op.add_column('pedidos', sa.Column('turno_caja_id', sa.Integer(), nullable=True))
    op.add_column('pedidos', sa.Column('numero_provisorio', sa.String(50), nullable=True))
    op.add_column('pedidos', sa.Column('diferencia_precio', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_foreign_key(
        'fk_pedidos_turno_caja_id', 'pedidos', 'turnos_caja',
        ['turno_caja_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index(
        'uq_pedidos_tenant_client_uuid', 'pedidos',
        ['tenant_id', 'client_uuid'], unique=True
    )
    op.create_index('ix_pedidos_turno_caja_id', 'pedidos', ['turno_caja_id'])


def downgrade():
    op.drop_index('ix_pedidos_turno_caja_id', table_name='pedidos')
    op.drop_index('uq_pedidos_tenant_client_uuid', table_name='pedidos')
    op.drop_constraint('fk_pedidos_turno_caja_id', 'pedidos', type_='foreignkey')
    op.drop_column('pedidos', 'diferencia_precio')
    op.drop_column('pedidos', 'numero_provisorio')
    op.drop_column('pedidos', 'turno_caja_id')
    op.drop_column('pedidos', 'origen')
    op.drop_column('pedidos', 'fecha_venta_cliente')
    op.drop_column('pedidos', 'client_uuid')
