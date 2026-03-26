"""add user_oauth_accounts table and make hashed_password nullable

Revision ID: a1b2c3d4e5f6
Revises: e1f2a3b4c5d6
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Hacer hashed_password nullable para usuarios que solo usan OAuth
    op.alter_column('users', 'hashed_password', nullable=True)

    # Crear tabla user_oauth_accounts
    op.create_table(
        'user_oauth_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_id', name='uq_oauth_provider_id'),
    )
    op.create_index('ix_user_oauth_accounts_id', 'user_oauth_accounts', ['id'])
    op.create_index('ix_user_oauth_accounts_user_id', 'user_oauth_accounts', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_user_oauth_accounts_user_id', table_name='user_oauth_accounts')
    op.drop_index('ix_user_oauth_accounts_id', table_name='user_oauth_accounts')
    op.drop_table('user_oauth_accounts')
    op.alter_column('users', 'hashed_password', nullable=False)
