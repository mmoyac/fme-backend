"""add_customer_address_and_order_notes

Revision ID: 9e72c2b2d9d3
Revises: 042fe92e014b
Create Date: 2025-11-24 15:47:01.268211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e72c2b2d9d3'
down_revision: Union[str, None] = '042fe92e014b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
