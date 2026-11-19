"""add tarifas_delivery y pedidos.comuna_entrega

Change OpenSpec: add-delivery-por-comuna (retiro o delivery por comuna en el checkout de la tienda)

Revision ID: d5a1c7e3f9b2
Revises: c4f8e2d6b1a9
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'd5a1c7e3f9b2'
down_revision = 'c4f8e2d6b1a9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tarifas_delivery',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('comuna', sa.String(100), nullable=False),
        sa.Column('comuna_normalizada', sa.String(100), nullable=False),
        sa.Column('costo', sa.Numeric(10, 0), nullable=False, server_default='0'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'comuna_normalizada', name='uq_tarifas_delivery_tenant_comuna'),
    )
    op.create_index('ix_tarifas_delivery_id', 'tarifas_delivery', ['id'])
    op.create_index('ix_tarifas_delivery_tenant_id', 'tarifas_delivery', ['tenant_id'])
    op.add_column('pedidos', sa.Column('comuna_entrega', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('pedidos', 'comuna_entrega')
    op.drop_index('ix_tarifas_delivery_tenant_id', table_name='tarifas_delivery')
    op.drop_index('ix_tarifas_delivery_id', table_name='tarifas_delivery')
    op.drop_table('tarifas_delivery')
