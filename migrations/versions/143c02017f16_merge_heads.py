"""merge heads

Revision ID: 143c02017f16
Revises: solicitudes_transferencia_20260226, 34797116272a
Create Date: 2026-02-26 16:10:05.009168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '143c02017f16'
down_revision: Union[str, None] = '34797116272a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
