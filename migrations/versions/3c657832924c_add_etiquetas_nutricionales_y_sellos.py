"""add_etiquetas_nutricionales_y_sellos

Revision ID: 3c657832924c
Revises: 2059846734ce
Create Date: 2026-02-17 18:41:52.906300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c657832924c'
down_revision: Union[str, None] = '2059846734ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla de sellos de advertencia
    op.create_table('sellos_advertencia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.Column('descripcion', sa.String(), nullable=True),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('icono', sa.String(), nullable=True),
    sa.Column('orden', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sellos_advertencia_codigo'), 'sellos_advertencia', ['codigo'], unique=True)
    op.create_index(op.f('ix_sellos_advertencia_id'), 'sellos_advertencia', ['id'], unique=False)
    
    # Crear tabla de información nutricional
    op.create_table('informacion_nutricional',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('producto_id', sa.Integer(), nullable=False),
    sa.Column('porcion_referencia', sa.String(), nullable=True),
    sa.Column('energia_kcal', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('proteinas_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('carbohidratos_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('azucares_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('grasas_totales_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('grasas_saturadas_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('grasas_trans_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('fibra_g', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('sodio_mg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('colesterol_mg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('calcio_mg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('hierro_mg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('vitamina_a_mcg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('vitamina_c_mg', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('producto_id')
    )
    op.create_index(op.f('ix_informacion_nutricional_id'), 'informacion_nutricional', ['id'], unique=False)
    
    # Crear tabla de relación producto-sellos
    op.create_table('producto_sellos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('producto_id', sa.Integer(), nullable=False),
    sa.Column('sello_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sello_id'], ['sellos_advertencia.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('producto_id', 'sello_id', name='uk_producto_sello')
    )
    op.create_index(op.f('ix_producto_sellos_id'), 'producto_sellos', ['id'], unique=False)


def downgrade() -> None:
    # Revertir tablas de etiquetas
    op.drop_index(op.f('ix_producto_sellos_id'), table_name='producto_sellos')
    op.drop_table('producto_sellos')
    op.drop_index(op.f('ix_informacion_nutricional_id'), table_name='informacion_nutricional')
    op.drop_table('informacion_nutricional')
    op.drop_index(op.f('ix_sellos_advertencia_id'), table_name='sellos_advertencia')
    op.drop_index(op.f('ix_sellos_advertencia_codigo'), table_name='sellos_advertencia')
    op.drop_table('sellos_advertencia')
    op.drop_constraint(None, 'clientes', type_='unique')
    op.create_index('ix_clientes_tenant_email_unique', 'clientes', ['tenant_id', 'email'], unique=False, postgresql_where='(email IS NOT NULL)')
    op.drop_index(op.f('ix_producto_sellos_id'), table_name='producto_sellos')
    op.drop_table('producto_sellos')
    op.drop_index(op.f('ix_informacion_nutricional_id'), table_name='informacion_nutricional')
    op.drop_table('informacion_nutricional')
    op.drop_index(op.f('ix_sellos_advertencia_id'), table_name='sellos_advertencia')
    op.drop_index(op.f('ix_sellos_advertencia_codigo'), table_name='sellos_advertencia')
    op.drop_table('sellos_advertencia')
    # ### end Alembic commands ###
