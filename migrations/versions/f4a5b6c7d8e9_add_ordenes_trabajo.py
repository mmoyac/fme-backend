"""add ordenes trabajo

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columna correlativo_ot en tenants (correlativo_cotizacion ya existe)
    op.add_column('tenants', sa.Column('correlativo_ot', sa.Integer(), nullable=False, server_default='0'))

    # Tabla ordenes_trabajo
    op.create_table(
        'ordenes_trabajo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('numero_ot', sa.String(50), nullable=False),
        sa.Column('tipo_ot_id', sa.Integer(), nullable=False),
        sa.Column('estado_ot_id', sa.Integer(), nullable=False),
        sa.Column('etapa_actual_id', sa.Integer(), nullable=True),
        sa.Column('local_id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=True),
        sa.Column('cotizacion_id', sa.Integer(), nullable=True),
        sa.Column('op_id', sa.Integer(), nullable=True),
        sa.Column('fecha_programada', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_inicio', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('creado_por_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tipo_ot_id'], ['tipos_ot.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['estado_ot_id'], ['estados_ot.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['etapa_actual_id'], ['ot_etapas_tipo.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['local_id'], ['locales.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cotizacion_id'], ['cotizaciones.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['op_id'], ['ordenes_produccion.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['creado_por_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_ordenes_trabajo_id', 'ordenes_trabajo', ['id'])
    op.create_index('ix_ordenes_trabajo_tenant_id', 'ordenes_trabajo', ['tenant_id'])
    op.create_index('ix_ordenes_trabajo_numero_ot', 'ordenes_trabajo', ['numero_ot'], unique=True)

    # Tabla ot_items
    op.create_table(
        'ot_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ot_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('unidad_medida_id', sa.Integer(), nullable=True),
        sa.Column('cantidad', sa.Numeric(10, 3), nullable=False),
        sa.Column('cantidad_ejecutada', sa.Numeric(10, 3), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ot_id'], ['ordenes_trabajo.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['unidad_medida_id'], ['unidades_medida.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_ot_items_id', 'ot_items', ['id'])
    op.create_index('ix_ot_items_ot_id', 'ot_items', ['ot_id'])

    # Tabla ot_log
    op.create_table(
        'ot_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ot_id', sa.Integer(), nullable=False),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('etapa_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ot_id'], ['ordenes_trabajo.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['etapa_id'], ['ot_etapas_tipo.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_ot_log_id', 'ot_log', ['id'])
    op.create_index('ix_ot_log_ot_id', 'ot_log', ['ot_id'])


def downgrade() -> None:
    op.drop_table('ot_log')
    op.drop_table('ot_items')
    op.drop_table('ordenes_trabajo')
    op.drop_column('tenants', 'correlativo_ot')
