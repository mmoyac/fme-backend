"""add modulos contratados por tenant

Change OpenSpec: add-modulos-tenant

- tenant_modulos: módulos contratados por tenant (catálogo en utils/modulos.py).
- menu_items.modulo: módulo al que pertenece cada ítem (NULL = núcleo), relleno por href.
- Todo tenant existente recibe los 12 módulos para que nadie pierda acceso.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-11-16

"""
from alembic import op
import sqlalchemy as sa

revision = 'd3e4f5a6b7c8'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None

# Copia fija (las migraciones no deben depender del código vivo).
MODULOS = (
    'ventas', 'cotizaciones', 'preventa', 'tienda_online', 'inventario', 'compras',
    'produccion', 'etiquetado', 'despacho', 'cobranza', 'comisiones', 'fidelizacion',
)
MODULO_POR_HREF = {
    '/admin/solicitudes': 'ventas',
    '/admin/pedidos': 'ventas',
    '/admin/pedidos/pos': 'ventas',
    '/admin/cotizaciones': 'cotizaciones',
    '/admin/pedidos/cajas': 'preventa',
    '/admin/inventario': 'inventario',
    '/admin/compras': 'compras',
    '/admin/facturas': 'compras',
    '/admin/recepcion': 'compras',
    '/admin/produccion': 'produccion',
    '/admin/produccion/ordenes-trabajo': 'produccion',
    '/admin/despacho': 'despacho',
    '/admin/cobranza': 'cobranza',
    '/admin/notas-credito': 'cobranza',
    '/admin/comisiones': 'comisiones',
}


def upgrade():
    lista = ", ".join(f"'{m}'" for m in MODULOS)
    op.create_table(
        'tenant_modulos',
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('modulo', sa.String(30), primary_key=True),
        sa.Column('activado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('activado_por', sa.String(255), nullable=True),
        sa.CheckConstraint(f"modulo IN ({lista})", name='ck_tenant_modulos_modulo'),
    )
    op.add_column('menu_items', sa.Column('modulo', sa.String(30), nullable=True))

    conn = op.get_bind()
    for href, modulo in MODULO_POR_HREF.items():
        conn.execute(
            sa.text("UPDATE menu_items SET modulo = :m WHERE href = :h"),
            {"m": modulo, "h": href},
        )
    for modulo in MODULOS:
        conn.execute(
            sa.text(
                "INSERT INTO tenant_modulos (tenant_id, modulo, activado_por) "
                "SELECT id, :m, 'migracion' FROM tenants ON CONFLICT DO NOTHING"
            ),
            {"m": modulo},
        )


def downgrade():
    op.drop_column('menu_items', 'modulo')
    op.drop_table('tenant_modulos')
