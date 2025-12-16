"""remove obsolete menu items

Revision ID: a6f7dbe92e02
Revises: 5938840ce1ec
Create Date: 2025-12-16 15:12:15.434146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6f7dbe92e02'
down_revision: Union[str, None] = '5938840ce1ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM menu_items WHERE href IN ('/admin/transferencias', '/admin/historial')")


def downgrade() -> None:
    pass
