"""add es_local_fabricacion to locales

Revision ID: a1b2c3d4e5f7
Revises: f4a5b6c7d8e9
Create Date: 2026-04-01 00:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('locales', sa.Column('es_local_fabricacion', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('locales', 'es_local_fabricacion')
