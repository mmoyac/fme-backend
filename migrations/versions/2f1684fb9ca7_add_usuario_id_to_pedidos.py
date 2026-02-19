"""add_usuario_id_to_pedidos

Revision ID: 2f1684fb9ca7
Revises: 354387271798
Create Date: 2026-02-17 20:48:24.589529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f1684fb9ca7'
down_revision: Union[str, None] = '354387271798'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna usuario_id a tabla pedidos
    op.add_column('pedidos', sa.Column('usuario_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_pedidos_usuario', 'pedidos', 'users', ['usuario_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Revertir cambios
    op.drop_constraint('fk_pedidos_usuario', 'pedidos', type_='foreignkey')
    op.drop_column('pedidos', 'usuario_id')
