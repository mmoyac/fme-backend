"""add rol produccion y trazabilidad en OP

Change OpenSpec: add-rol-produccion-op

- ordenes_produccion.solicitado_por_id / producido_por_id: FK opcional a users.
- detalles_orden_produccion.motivo_diferencia: motivo opcional por detalle.
- Rol `produccion` en cada tenant (idempotente) con permiso al menú /admin/produccion
  (y sus submenús /admin/produccion/*) si existen.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-11-16

"""
from alembic import op
import sqlalchemy as sa

revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ordenes_produccion', sa.Column(
        'solicitado_por_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('ordenes_produccion', sa.Column(
        'producido_por_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('detalles_orden_produccion', sa.Column('motivo_diferencia', sa.Text(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO roles (tenant_id, nombre, descripcion)
        SELECT t.id, 'produccion', 'Producción: informa cantidades reales de las órdenes de producción'
        FROM tenants t
        WHERE NOT EXISTS (
            SELECT 1 FROM roles r WHERE r.tenant_id = t.id AND r.nombre = 'produccion'
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO role_menu_permissions (role_id, menu_item_id)
        SELECT r.id, m.id
        FROM roles r
        CROSS JOIN menu_items m
        WHERE r.nombre = 'produccion'
          AND (m.href = '/admin/produccion' OR m.href LIKE '/admin/produccion/%')
          AND NOT EXISTS (
              SELECT 1 FROM role_menu_permissions p
              WHERE p.role_id = r.id AND p.menu_item_id = m.id
          )
    """))


def downgrade():
    conn = op.get_bind()
    # Elimina el rol solo si no tiene usuarios asignados
    conn.execute(sa.text("""
        DELETE FROM roles r
        WHERE r.nombre = 'produccion'
          AND NOT EXISTS (SELECT 1 FROM users u WHERE u.role_id = r.id)
    """))
    op.drop_column('detalles_orden_produccion', 'motivo_diferencia')
    op.drop_column('ordenes_produccion', 'producido_por_id')
    op.drop_column('ordenes_produccion', 'solicitado_por_id')
