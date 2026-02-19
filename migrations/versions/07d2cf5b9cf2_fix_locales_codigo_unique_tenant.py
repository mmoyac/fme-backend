"""fix_locales_codigo_unique_tenant

Revision ID: 07d2cf5b9cf2
Revises: 2b1dd40d8384
Create Date: 2026-02-01 00:17:26.039758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07d2cf5b9cf2'
down_revision: Union[str, None] = '2b1dd40d8384'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar constraint UNIQUE de codigo
    op.drop_index('ix_locales_codigo', table_name='locales')
    
    # Crear índice compuesto UNIQUE para (tenant_id, codigo)
    op.create_index(
        'ix_locales_tenant_codigo_unique',
        'locales',
        ['tenant_id', 'codigo'],
        unique=True
    )
    
    # Recrear índice no-único para codigo solo (para búsquedas)
    op.create_index('ix_locales_codigo', 'locales', ['codigo'], unique=False)


def downgrade() -> None:
    # Revertir cambios
    op.drop_index('ix_locales_codigo', table_name='locales')
    op.drop_index('ix_locales_tenant_codigo_unique', table_name='locales')
    
    # Restaurar índice único original
    op.create_index('ix_locales_codigo', 'locales', ['codigo'], unique=True)
