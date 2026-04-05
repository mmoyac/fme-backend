"""add cotizaciones y ordenes_trabajo etapa1: tipos_ot, estados_cotizacion, estados_ot, ot_etapas_tipo

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-03-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------
    # 1. tipos_ot (maestra global)
    # --------------------------------------------------
    op.create_table(
        'tipos_ot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.String(255), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tipos_ot_id', 'tipos_ot', ['id'])
    op.create_index('ix_tipos_ot_codigo', 'tipos_ot', ['codigo'], unique=True)

    # Seed: OP y OS
    op.execute("""
        INSERT INTO tipos_ot (codigo, nombre, descripcion, activo) VALUES
        ('OP', 'Orden de Producción', 'Producción de productos con receta y materias primas', true),
        ('OS', 'Orden de Servicio', 'Servicio o productos elaborados que solo rebajan stock', true)
    """)

    # --------------------------------------------------
    # 2. estados_cotizacion (maestra global)
    # --------------------------------------------------
    op.create_table(
        'estados_cotizacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(50), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('color', sa.String(20), nullable=False, server_default='gray-500'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('es_final', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_estados_cotizacion_id', 'estados_cotizacion', ['id'])
    op.create_index('ix_estados_cotizacion_codigo', 'estados_cotizacion', ['codigo'], unique=True)

    # Seed
    op.execute("""
        INSERT INTO estados_cotizacion (codigo, nombre, color, orden, es_final) VALUES
        ('BORRADOR',  'Borrador',            'gray-400',   1, false),
        ('ENVIADA',   'Enviada al cliente',  'blue-500',   2, false),
        ('ACEPTADA',  'Aceptada',            'green-500',  3, true),
        ('RECHAZADA', 'Rechazada',           'red-500',    4, true),
        ('VENCIDA',   'Vencida',             'orange-400', 5, true)
    """)

    # --------------------------------------------------
    # 3. estados_ot (maestra global)
    # --------------------------------------------------
    op.create_table(
        'estados_ot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(50), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('color', sa.String(20), nullable=False, server_default='gray-500'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('es_final', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_estados_ot_id', 'estados_ot', ['id'])
    op.create_index('ix_estados_ot_codigo', 'estados_ot', ['codigo'], unique=True)

    # Seed
    op.execute("""
        INSERT INTO estados_ot (codigo, nombre, color, orden, es_final) VALUES
        ('PENDIENTE',   'Pendiente',   'gray-400',   1, false),
        ('EN_PROCESO',  'En proceso',  'blue-500',   2, false),
        ('TERMINADA',   'Terminada',   'green-400',  3, false),
        ('CERRADA',     'Cerrada',     'green-700',  4, true),
        ('CANCELADA',   'Cancelada',   'red-500',    5, true)
    """)

    # --------------------------------------------------
    # 4. ot_etapas_tipo (parametrizable por tenant y tipo_ot)
    # --------------------------------------------------
    op.create_table(
        'ot_etapas_tipo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo_ot_id', sa.Integer(), sa.ForeignKey('tipos_ot.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('es_etapa_final', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('color', sa.String(10), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ot_etapas_tipo_id', 'ot_etapas_tipo', ['id'])
    op.create_index('ix_ot_etapas_tipo_tenant_id', 'ot_etapas_tipo', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_ot_etapas_tipo_tenant_id', table_name='ot_etapas_tipo')
    op.drop_index('ix_ot_etapas_tipo_id', table_name='ot_etapas_tipo')
    op.drop_table('ot_etapas_tipo')

    op.drop_index('ix_estados_ot_codigo', table_name='estados_ot')
    op.drop_index('ix_estados_ot_id', table_name='estados_ot')
    op.drop_table('estados_ot')

    op.drop_index('ix_estados_cotizacion_codigo', table_name='estados_cotizacion')
    op.drop_index('ix_estados_cotizacion_id', table_name='estados_cotizacion')
    op.drop_table('estados_cotizacion')

    op.drop_index('ix_tipos_ot_codigo', table_name='tipos_ot')
    op.drop_index('ix_tipos_ot_id', table_name='tipos_ot')
    op.drop_table('tipos_ot')
