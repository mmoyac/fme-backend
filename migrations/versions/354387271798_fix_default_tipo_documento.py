"""fix_default_tipo_documento

Revision ID: 354387271798
Revises: 3c657832924c
Create Date: 2026-02-17 20:12:35.068642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '354387271798'
down_revision: Union[str, None] = '3c657832924c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cambiar default de tipo_documento_tributario_id de 1 (FAC) a 2 (BOL)
    op.alter_column('pedidos', 'tipo_documento_tributario_id',
                    existing_type=sa.INTEGER(),
                    server_default='2',
                    existing_nullable=True)


def downgrade() -> None:
    # Revertir default de tipo_documento_tributario_id de 2 (BOL) a 1 (FAC)
    op.alter_column('pedidos', 'tipo_documento_tributario_id',
                    existing_type=sa.INTEGER(),
                    server_default='1',
                    existing_nullable=True)
