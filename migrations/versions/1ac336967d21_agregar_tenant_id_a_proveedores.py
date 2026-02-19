"""agregar_tenant_id_a_proveedores

Revision ID: 1ac336967d21
Revises: 163001ab85d7
Create Date: 2026-01-31 23:11:34.251727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ac336967d21'
down_revision: Union[str, None] = '163001ab85d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna tenant_id a proveedores
    op.add_column('proveedores', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_proveedores_tenant', 'proveedores', 'tenants', ['tenant_id'], ['id'])
    
    # Asignar todos los proveedores existentes al tenant 1 (Masas Estación)
    op.execute("UPDATE proveedores SET tenant_id = 1")
    
    # Hacer la columna NOT NULL después de la actualización
    op.alter_column('proveedores', 'tenant_id', nullable=False)


def downgrade() -> None:
    op.drop_constraint('fk_proveedores_tenant', 'proveedores', type_='foreignkey')
    op.drop_column('proveedores', 'tenant_id')
