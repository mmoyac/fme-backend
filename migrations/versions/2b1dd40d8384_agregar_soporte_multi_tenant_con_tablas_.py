"""Agregar soporte multi-tenant con tablas tenants y configuracion_landing

Revision ID: 2b1dd40d8384
Revises: 559922158ab7
Create Date: 2026-01-31 23:37:38.295835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2b1dd40d8384'
down_revision: Union[str, None] = '559922158ab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PASO 1: Crear tabla tenants
    op.create_table('tenants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('dominio_principal', sa.String(length=100), nullable=True),
    sa.Column('subdomain', sa.String(length=50), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dominio_principal'),
    sa.UniqueConstraint('subdomain')
    )
    op.create_index(op.f('ix_tenants_codigo'), 'tenants', ['codigo'], unique=True)
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_nombre'), 'tenants', ['nombre'], unique=False)
    
    # PASO 2: Insertar tenant inicial (Masas Estación)
    op.execute("""
        INSERT INTO tenants (id, codigo, nombre, dominio_principal, subdomain, activo)
        VALUES (1, 'masas-estacion', 'Masas Estación', 'masasestacion.cl', 'masasestacion', true)
    """)
    
    # PASO 3: Crear tabla configuracion_landing
    op.create_table('configuracion_landing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('logo_url', sa.String(length=255), nullable=True),
    sa.Column('favicon_url', sa.String(length=255), nullable=True),
    sa.Column('nombre_comercial', sa.String(length=100), nullable=True),
    sa.Column('colores', postgresql.JSON(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('hero_titulo', sa.Text(), nullable=True),
    sa.Column('hero_subtitulo', sa.Text(), nullable=True),
    sa.Column('hero_imagen_url', sa.String(length=255), nullable=True),
    sa.Column('hero_cta_texto', sa.String(length=50), nullable=True),
    sa.Column('hero_cta_link', sa.String(length=100), nullable=True),
    sa.Column('hero_badges', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('beneficios', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('redes_sociales', postgresql.JSON(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('telefono', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('direccion', sa.Text(), nullable=True),
    sa.Column('texto_footer_descripcion', sa.Text(), nullable=True),
    sa.Column('texto_copyright', sa.String(length=200), nullable=True),
    sa.Column('meta_title', sa.String(length=100), nullable=True),
    sa.Column('meta_description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id')
    )
    op.create_index(op.f('ix_configuracion_landing_id'), 'configuracion_landing', ['id'], unique=False)
    
    # PASO 4: Agregar columna tenant_id como NULL temporalmente
    op.add_column('clientes', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.add_column('locales', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.add_column('pedidos', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.add_column('productos', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('tenant_id', sa.Integer(), nullable=True))
    
    # PASO 5: Asignar tenant_id = 1 a todos los datos existentes
    op.execute("UPDATE clientes SET tenant_id = 1")
    op.execute("UPDATE locales SET tenant_id = 1")
    op.execute("UPDATE pedidos SET tenant_id = 1")
    op.execute("UPDATE productos SET tenant_id = 1")
    op.execute("UPDATE users SET tenant_id = 1")
    
    # PASO 6: Hacer las columnas NOT NULL y agregar constraints
    op.alter_column('clientes', 'tenant_id', nullable=False)
    op.alter_column('locales', 'tenant_id', nullable=False)
    op.alter_column('pedidos', 'tenant_id', nullable=False)
    op.alter_column('productos', 'tenant_id', nullable=False)
    op.alter_column('users', 'tenant_id', nullable=False)
    
    # PASO 7: Crear índices y foreign keys
    op.create_index(op.f('ix_clientes_tenant_id'), 'clientes', ['tenant_id'], unique=False)
    op.create_foreign_key(None, 'clientes', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    
    op.create_index(op.f('ix_locales_tenant_id'), 'locales', ['tenant_id'], unique=False)
    op.create_foreign_key(None, 'locales', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    
    op.create_index(op.f('ix_pedidos_tenant_id'), 'pedidos', ['tenant_id'], unique=False)
    op.create_foreign_key(None, 'pedidos', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    
    op.create_index(op.f('ix_productos_tenant_id'), 'productos', ['tenant_id'], unique=False)
    op.create_foreign_key(None, 'productos', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_foreign_key(None, 'users', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_column('users', 'tenant_id')
    op.drop_constraint(None, 'productos', type_='foreignkey')
    op.drop_index(op.f('ix_productos_tenant_id'), table_name='productos')
    op.drop_column('productos', 'tenant_id')
    op.drop_constraint(None, 'pedidos', type_='foreignkey')
    op.drop_index(op.f('ix_pedidos_tenant_id'), table_name='pedidos')
    op.drop_column('pedidos', 'tenant_id')
    op.drop_constraint(None, 'locales', type_='foreignkey')
    op.drop_index(op.f('ix_locales_tenant_id'), table_name='locales')
    op.drop_column('locales', 'tenant_id')
    op.drop_constraint(None, 'clientes', type_='foreignkey')
    op.drop_index(op.f('ix_clientes_tenant_id'), table_name='clientes')
    op.drop_column('clientes', 'tenant_id')
    op.drop_index(op.f('ix_configuracion_landing_id'), table_name='configuracion_landing')
    op.drop_table('configuracion_landing')
    op.drop_index(op.f('ix_tenants_nombre'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_id'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_codigo'), table_name='tenants')
    op.drop_table('tenants')
    # ### end Alembic commands ###
