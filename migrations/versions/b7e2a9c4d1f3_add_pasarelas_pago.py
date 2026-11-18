"""add pasarelas de pago e intenciones de pago en línea

Change OpenSpec: add-pasarelas-pago (arquitectura multipasarela portada de EffiCheck)

- pasarelas_pago: pasarela por tenant (proveedor, ambiente, credenciales cifradas, prueba de conexión, activo).
- pagos_online: intención de pago de un pedido (estado, vencimiento, orden del comercio, datos del proveedor).
- medios_pago: FLOW, KHIPU y PAGO_ONLINE (inactivos: solo registran el medio de los pedidos pagados en línea,
  no se ofrecen en POS/backoffice). MERCADOPAGO ya existía.

Revision ID: b7e2a9c4d1f3
Revises: f5a6b7c8d9e0
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b7e2a9c4d1f3'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pasarelas_pago',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('proveedor', sa.String(20), nullable=False),
        sa.Column('nombre_visible', sa.String(60), nullable=False),
        sa.Column('ambiente', sa.String(12), nullable=False, server_default='INTEGRACION'),
        sa.Column('credenciales_cifradas', sa.LargeBinary(), nullable=True),
        sa.Column('credenciales_actualizadas_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ultima_prueba_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultima_prueba_ok', sa.Boolean(), nullable=True),
        sa.Column('ultima_prueba_mensaje', sa.String(300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("ambiente IN ('INTEGRACION', 'PRODUCCION')", name='ck_pasarelas_pago_ambiente'),
    )
    op.create_table(
        'pagos_online',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('pedido_id', sa.Integer(), sa.ForeignKey('pedidos.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('pasarela_id', sa.Integer(), sa.ForeignKey('pasarelas_pago.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('monto', sa.Numeric(12, 0), nullable=False),
        sa.Column('estado', sa.String(12), nullable=False, server_default='INICIADO'),
        sa.Column('iniciado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expira_en', sa.DateTime(timezone=True), nullable=False),
        sa.Column('orden_comercio', sa.String(26), nullable=False),
        sa.Column('email_pagador', sa.String(255), nullable=True),
        sa.Column('url_sitio', sa.String(255), nullable=True),
        sa.Column('url_pago', sa.Text(), nullable=True),
        sa.Column('token_pasarela', sa.String(200), nullable=True),
        sa.Column('id_transaccion_proveedor', sa.String(100), nullable=True),
        sa.Column('codigo_autorizacion', sa.String(60), nullable=True),
        sa.Column('ultimos_digitos', sa.String(8), nullable=True),
        sa.Column('respuesta_proveedor', postgresql.JSONB(), nullable=True),
        sa.Column('monto_confirmado', sa.Numeric(12, 0), nullable=True),
        sa.Column('confirmado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_revision', sa.String(300), nullable=True),
        sa.UniqueConstraint('orden_comercio', name='uq_pagos_online_orden_comercio'),
        sa.CheckConstraint("estado IN ('INICIADO', 'CONFIRMADO', 'RECHAZADO', 'EXPIRADO', 'EN_REVISION')",
                           name='ck_pagos_online_estado'),
    )
    op.create_index('ix_pagos_online_pasarela_token', 'pagos_online', ['pasarela_id', 'token_pasarela'])
    op.create_index('ix_pagos_online_estado', 'pagos_online', ['estado', 'iniciado_en'])

    op.execute("""
        INSERT INTO medios_pago (codigo, nombre, descripcion, permite_cheque, es_contado, plazo_dias, activo)
        SELECT v.codigo, v.nombre, v.descripcion, false, true, 0, false
        FROM (VALUES ('FLOW', 'Flow', 'Pago en línea con Flow'),
                     ('KHIPU', 'Khipu', 'Pago en línea con Khipu (transferencia)'),
                     ('PAGO_ONLINE', 'Pago en línea', 'Pago en línea (otras pasarelas)')) AS v(codigo, nombre, descripcion)
        WHERE NOT EXISTS (SELECT 1 FROM medios_pago m WHERE m.codigo = v.codigo)
    """)


def downgrade():
    op.drop_index('ix_pagos_online_estado', table_name='pagos_online')
    op.drop_index('ix_pagos_online_pasarela_token', table_name='pagos_online')
    op.drop_table('pagos_online')
    op.drop_table('pasarelas_pago')
    op.execute("DELETE FROM medios_pago WHERE codigo IN ('FLOW', 'KHIPU', 'PAGO_ONLINE') "
               "AND NOT EXISTS (SELECT 1 FROM pedidos p WHERE p.medio_pago_id = medios_pago.id)")
