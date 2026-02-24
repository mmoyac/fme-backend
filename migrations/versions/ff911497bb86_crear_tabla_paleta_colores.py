"""crear tabla paleta_colores

Revision ID: ff911497bb86
Revises: 6d5e03d2ec23
Create Date: 2026-02-24 01:31:14.076962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff911497bb86'
down_revision: Union[str, None] = '6d5e03d2ec23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla paleta_colores
    op.create_table(
        'paleta_colores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('primario', sa.String(length=10), nullable=False),
        sa.Column('primario_light', sa.String(length=10), nullable=True),
        sa.Column('primario_dark', sa.String(length=10), nullable=True),
        sa.Column('secundario', sa.String(length=10), nullable=False),
        sa.Column('secundario_light', sa.String(length=10), nullable=True),
        sa.Column('secundario_dark', sa.String(length=10), nullable=True),
        sa.Column('acento', sa.String(length=10), nullable=True),
        sa.Column('fondo_hero_inicio', sa.String(length=10), nullable=True),
        sa.Column('fondo_hero_fin', sa.String(length=10), nullable=True),
        sa.Column('fondo_seccion', sa.String(length=10), nullable=True),
        sa.Column('es_publica', sa.Boolean(), nullable=False),
        sa.Column('creado_por', sa.Integer(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['creado_por'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # Crear índices para paleta_colores
    op.create_index(op.f('ix_paleta_colores_id'), 'paleta_colores', ['id'], unique=False)
    op.create_index(op.f('ix_paleta_colores_nombre'), 'paleta_colores', ['nombre'], unique=True)


def downgrade() -> None:
    # Eliminar índices de paleta_colores
    op.drop_index(op.f('ix_paleta_colores_nombre'), table_name='paleta_colores')
    op.drop_index(op.f('ix_paleta_colores_id'), table_name='paleta_colores')
    # Eliminar tabla paleta_colores
    op.drop_table('paleta_colores')
