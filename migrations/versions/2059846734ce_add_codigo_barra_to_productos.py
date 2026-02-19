"""add_codigo_barra_to_productos

Revision ID: 2059846734ce
Revises: 6782251ed843
Create Date: 2026-02-17 18:30:24.164194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2059846734ce'
down_revision: Union[str, None] = '6782251ed843'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar campo codigo_barra a productos
    op.add_column('productos', sa.Column('codigo_barra', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_productos_codigo_barra'), 'productos', ['codigo_barra'], unique=False)


def downgrade() -> None:
    # Revertir cambios de codigo_barra
    op.drop_index(op.f('ix_productos_codigo_barra'), table_name='productos')
    op.drop_column('productos', 'codigo_barra')
