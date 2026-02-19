"""fix_unique_constraints_multi_tenant

Revision ID: 163001ab85d7
Revises: 07d2cf5b9cf2
Create Date: 2026-02-01 00:18:05.505158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '163001ab85d7'
down_revision: Union[str, None] = '07d2cf5b9cf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === PRODUCTOS: SKU debe ser único por tenant ===
    # 1. Eliminar constraint UNIQUE de sku
    op.drop_index('ix_productos_sku', table_name='productos')
    
    # 2. Crear índice compuesto UNIQUE para (tenant_id, sku)
    op.create_index(
        'ix_productos_tenant_sku_unique',
        'productos',
        ['tenant_id', 'sku'],
        unique=True
    )
    
    # 3. Recrear índice no-único para sku solo (para búsquedas)
    op.create_index('ix_productos_sku', 'productos', ['sku'], unique=False)
    
    # === LOCALES: nombre debe ser único por tenant ===
    # 1. Eliminar constraint UNIQUE de nombre
    op.drop_index('ix_locales_nombre', table_name='locales')
    
    # 2. Crear índice compuesto UNIQUE para (tenant_id, nombre)
    op.create_index(
        'ix_locales_tenant_nombre_unique',
        'locales',
        ['tenant_id', 'nombre'],
        unique=True
    )
    
    # 3. Recrear índice no-único para nombre solo (para búsquedas)
    op.create_index('ix_locales_nombre', 'locales', ['nombre'], unique=False)
    
    # === CLIENTES: email debe ser único por tenant ===
    # 1. Eliminar constraint UNIQUE de email (si existe)
    try:
        op.drop_constraint('clientes_email_key', 'clientes', type_='unique')
    except:
        pass  # El constraint puede no existir
    
    # 2. Crear índice compuesto UNIQUE para (tenant_id, email)
    op.create_index(
        'ix_clientes_tenant_email_unique',
        'clientes',
        ['tenant_id', 'email'],
        unique=True,
        postgresql_where=sa.text('email IS NOT NULL')  # Solo si email no es NULL
    )


def downgrade() -> None:
    # Revertir todos los cambios
    
    # Productos
    op.drop_index('ix_productos_sku', table_name='productos')
    op.drop_index('ix_productos_tenant_sku_unique', table_name='productos')
    op.create_index('ix_productos_sku', 'productos', ['sku'], unique=True)
    
    # Locales
    op.drop_index('ix_locales_nombre', table_name='locales')
    op.drop_index('ix_locales_tenant_nombre_unique', table_name='locales')
    op.create_index('ix_locales_nombre', 'locales', ['nombre'], unique=True)
    
    # Clientes
    op.drop_index('ix_clientes_tenant_email_unique', table_name='clientes')
    op.create_unique_constraint('clientes_email_key', 'clientes', ['email'])
