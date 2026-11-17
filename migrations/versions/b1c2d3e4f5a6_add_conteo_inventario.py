"""add conteo de inventario

Change OpenSpec: add-conteo-inventario

- conteos_inventario: cabecera del conteo físico por local (COMPLETO/PARCIAL),
  estado EN_PROCESO/FINALIZADO/CANCELADO y auditoría de usuarios/fechas.
  Índice único parcial: un solo conteo EN_PROCESO por local.
- conteo_inventario_items: líneas (stock sistema vs contado, diferencia, ajuste aplicado,
  usuario y fecha de captura).
- movimientos_inventario.usuario_id: FK opcional a users para auditoría.

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-11-16

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = 'a9b8c7d6e5f4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'conteos_inventario',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('local_id', sa.Integer(), sa.ForeignKey('locales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('tipo', sa.String(10), nullable=False),
        sa.Column('estado', sa.String(15), nullable=False, server_default='EN_PROCESO'),
        sa.Column('observacion', sa.Text(), nullable=True),
        sa.Column('usuario_creador_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('usuario_cierre_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_conteos_inventario_id', 'conteos_inventario', ['id'])
    op.create_index('ix_conteos_inventario_tenant_id', 'conteos_inventario', ['tenant_id'])
    op.create_index('ix_conteos_inventario_local_id', 'conteos_inventario', ['local_id'])
    op.create_index('ix_conteos_inventario_estado', 'conteos_inventario', ['estado'])
    op.create_index(
        'uq_conteo_local_en_proceso', 'conteos_inventario', ['local_id'],
        unique=True, postgresql_where=sa.text("estado = 'EN_PROCESO'")
    )

    op.create_table(
        'conteo_inventario_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conteo_id', sa.Integer(), sa.ForeignKey('conteos_inventario.id', ondelete='CASCADE'), nullable=False),
        sa.Column('producto_id', sa.Integer(), sa.ForeignKey('productos.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('stock_sistema', sa.Numeric(10, 3), nullable=True),
        sa.Column('cantidad_contada', sa.Numeric(10, 3), nullable=True),
        sa.Column('diferencia', sa.Numeric(10, 3), nullable=True),
        sa.Column('ajuste_aplicado', sa.Numeric(10, 3), nullable=True),
        sa.Column('usuario_captura_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('fecha_captura', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('conteo_id', 'producto_id', name='uq_conteo_item_producto'),
    )
    op.create_index('ix_conteo_inventario_items_id', 'conteo_inventario_items', ['id'])
    op.create_index('ix_conteo_inventario_items_conteo_id', 'conteo_inventario_items', ['conteo_id'])

    op.add_column('movimientos_inventario', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_movimientos_inventario_usuario_id', 'movimientos_inventario', 'users',
        ['usuario_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_movimientos_inventario_usuario_id', 'movimientos_inventario', type_='foreignkey')
    op.drop_column('movimientos_inventario', 'usuario_id')
    op.drop_table('conteo_inventario_items')
    op.drop_index('uq_conteo_local_en_proceso', table_name='conteos_inventario')
    op.drop_table('conteos_inventario')
