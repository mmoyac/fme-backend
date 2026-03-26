"""add is_superadmin to users

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-03-25 12:00:00.000000

Agrega:
- Campo is_superadmin en users: identifica usuarios plataforma con acceso cross-tenant
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default='false',
                  comment='Super administrador de la plataforma. Tiene acceso cross-tenant.')
    )


def downgrade() -> None:
    op.drop_column('users', 'is_superadmin')
