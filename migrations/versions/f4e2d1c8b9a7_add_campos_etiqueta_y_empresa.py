"""add_campos_etiqueta_y_empresa

Revision ID: f4e2d1c8b9a7
Revises: a7933ae95522
Create Date: 2026-03-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4e2d1c8b9a7'
down_revision: Union[str, None] = 'a7933ae95522'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nuevos campos en informacion_nutricional
    op.add_column('informacion_nutricional', sa.Column('grasas_monoinsaturadas_g', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('grasas_poliinsaturadas_g', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('porciones_por_envase', sa.Integer(), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('porcion_peso_g', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('contenido_neto', sa.String(length=50), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('ingredientes', sa.Text(), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('alergenos', sa.Text(), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('modo_uso', sa.Text(), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('condiciones_almacenamiento', sa.Text(), nullable=True))
    op.add_column('informacion_nutricional', sa.Column('plazo_duracion', sa.Text(), nullable=True))

    # Nuevos campos en configuracion_landing
    op.add_column('configuracion_landing', sa.Column('razon_social', sa.String(length=200), nullable=True))
    op.add_column('configuracion_landing', sa.Column('resolucion_sanitaria', sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column('configuracion_landing', 'resolucion_sanitaria')
    op.drop_column('configuracion_landing', 'razon_social')

    op.drop_column('informacion_nutricional', 'plazo_duracion')
    op.drop_column('informacion_nutricional', 'condiciones_almacenamiento')
    op.drop_column('informacion_nutricional', 'modo_uso')
    op.drop_column('informacion_nutricional', 'alergenos')
    op.drop_column('informacion_nutricional', 'ingredientes')
    op.drop_column('informacion_nutricional', 'contenido_neto')
    op.drop_column('informacion_nutricional', 'porcion_peso_g')
    op.drop_column('informacion_nutricional', 'porciones_por_envase')
    op.drop_column('informacion_nutricional', 'grasas_poliinsaturadas_g')
    op.drop_column('informacion_nutricional', 'grasas_monoinsaturadas_g')
