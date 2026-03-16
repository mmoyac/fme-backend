"""add canal_venta and delivery fields

Revision ID: c3d1e8f2a7b9
Revises: b1c4d7e2f3a5
Create Date: 2026-03-16 10:00:00.000000

Agrega:
- Tabla maestra canales_venta (POS, LANDING, WHATSAPP, TELEFONO)
- FK canal_venta_id en pedidos
- Campo costo_delivery en pedidos (cobro aparte, no suma al total)
- Campos de configuracion de delivery en configuracion_landing
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d1e8f2a7b9'
down_revision: Union[str, None] = 'b1c4d7e2f3a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Crear tabla canales_venta
    op.create_table(
        'canales_venta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_canales_venta_id', 'canales_venta', ['id'])
    op.create_index('ix_canales_venta_codigo', 'canales_venta', ['codigo'], unique=True)

    # 2. Insertar datos iniciales
    op.execute("""
        INSERT INTO canales_venta (id, codigo, nombre, activo) VALUES
        (1, 'POS',      'Punto de Venta',  true),
        (2, 'LANDING',  'Tienda Online',   true),
        (3, 'WHATSAPP', 'WhatsApp',        true),
        (4, 'TELEFONO', 'Teléfono',        true)
    """)

    # 3. Agregar canal_venta_id a pedidos
    op.add_column(
        'pedidos',
        sa.Column('canal_venta_id', sa.Integer(), sa.ForeignKey('canales_venta.id', ondelete='SET NULL'), nullable=True)
    )

    # 4. Agregar costo_delivery a pedidos
    op.add_column(
        'pedidos',
        sa.Column('costo_delivery', sa.Numeric(10, 2), nullable=True,
                  comment='Costo de delivery acordado con el cliente. Cobro aparte, no suma al monto_total.')
    )

    # 5. Agregar campos de configuracion de delivery a configuracion_landing
    op.add_column('configuracion_landing', sa.Column('costo_fijo_delivery', sa.Numeric(10, 2), nullable=True))
    op.add_column('configuracion_landing', sa.Column('costo_por_km_delivery', sa.Numeric(10, 2), nullable=True))
    op.add_column('configuracion_landing', sa.Column('monto_minimo_delivery_gratis', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('configuracion_landing', 'monto_minimo_delivery_gratis')
    op.drop_column('configuracion_landing', 'costo_por_km_delivery')
    op.drop_column('configuracion_landing', 'costo_fijo_delivery')
    op.drop_column('pedidos', 'costo_delivery')
    op.drop_column('pedidos', 'canal_venta_id')
    op.drop_index('ix_canales_venta_codigo', table_name='canales_venta')
    op.drop_index('ix_canales_venta_id', table_name='canales_venta')
    op.drop_table('canales_venta')
