"""add verificaciones_email (código de verificación del correo en el checkout)

Change OpenSpec: add-pasarelas-pago (verificación del correo del cliente anónimo de la tienda)

Revision ID: c4f8e2d6b1a9
Revises: b7e2a9c4d1f3
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4f8e2d6b1a9'
down_revision = 'b7e2a9c4d1f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'verificaciones_email',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('codigo_hash', sa.String(64), nullable=False),
        sa.Column('expira_en', sa.DateTime(timezone=True), nullable=False),
        sa.Column('intentos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('verificado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anulado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ip', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_verificaciones_email_tenant_email', 'verificaciones_email', ['tenant_id', 'email', 'created_at'])


def downgrade():
    op.drop_index('ix_verificaciones_email_tenant_email', table_name='verificaciones_email')
    op.drop_table('verificaciones_email')
