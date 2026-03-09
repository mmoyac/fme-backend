"""fix_vehiculos_fk_to_tipos_vehiculo

Revision ID: f4503dd6bdfa
Revises: cac50f9a5746
Create Date: 2026-03-09 19:57:35.776573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4503dd6bdfa'
down_revision: Union[str, None] = 'cac50f9a5746'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the incorrect FK pointing to the duplicate table 'tipo_vehiculo'
    op.drop_constraint('vehiculos_tipo_vehiculo_id_fkey', 'vehiculos', type_='foreignkey')

    # 2. Drop the duplicate empty table created by the previous migration
    op.drop_index('ix_tipo_vehiculo_id', table_name='tipo_vehiculo')
    op.drop_table('tipo_vehiculo')

    # 3. Add the correct FK pointing to the real 'tipos_vehiculo' table
    op.create_foreign_key(
        'vehiculos_tipo_vehiculo_id_fkey',
        'vehiculos', 'tipos_vehiculo',
        ['tipo_vehiculo_id'], ['id'],
        ondelete='RESTRICT'
    )


def downgrade() -> None:
    op.drop_constraint('vehiculos_tipo_vehiculo_id_fkey', 'vehiculos', type_='foreignkey')

    op.create_table(
        'tipo_vehiculo',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tipo_vehiculo_id', 'tipo_vehiculo', ['id'], unique=False)

    op.create_foreign_key(
        'vehiculos_tipo_vehiculo_id_fkey',
        'vehiculos', 'tipo_vehiculo',
        ['tipo_vehiculo_id'], ['id'],
        ondelete='RESTRICT'
    )
