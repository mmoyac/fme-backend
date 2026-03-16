"""roles tenant scoped

Revision ID: a8b3c9d2e1f4
Revises: 6782251ed843
Create Date: 2026-03-13 10:00:00.000000

Agrega tenant_id a la tabla roles para que los roles/permisos sean
independientes por tenant. Los roles existentes se clonan para cada tenant.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a8b3c9d2e1f4'
down_revision: Union[str, None] = '79f6c6112c15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Agregar columna tenant_id como nullable primero
    op.add_column('roles', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_roles_tenant_id',
        'roles', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )

    # 2. Obtener conexión para manipular datos
    conn = op.get_bind()

    # 3. Obtener todos los tenants
    tenants = conn.execute(sa.text("SELECT id FROM tenants ORDER BY id")).fetchall()
    tenant_ids = [row[0] for row in tenants]

    if not tenant_ids:
        # Sin tenants, nada que migrar
        return

    # 4. Asignar los roles actuales al primer tenant (tenant_id=1 o el primero)
    first_tenant_id = tenant_ids[0]
    conn.execute(sa.text(
        "UPDATE roles SET tenant_id = :tid WHERE tenant_id IS NULL"
    ), {"tid": first_tenant_id})

    # 4b. Eliminar índices/constraints únicos en nombre ANTES de clonar
    #     (pueden llamarse de distintas formas según cómo se crearon)
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_roles_nombre"))
    conn.execute(sa.text("ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_nombre_key"))
    conn.execute(sa.text("ALTER TABLE roles DROP CONSTRAINT IF EXISTS uq_role_nombre"))

    # 5. Para cada tenant adicional, clonar todos los roles del primer tenant
    #    junto con sus permisos de menú
    for tenant_id in tenant_ids[1:]:
        # Obtener roles del primer tenant
        roles = conn.execute(sa.text(
            "SELECT id, nombre, descripcion FROM roles WHERE tenant_id = :tid"
        ), {"tid": first_tenant_id}).fetchall()

        for role in roles:
            old_role_id = role[0]
            nombre = role[1]
            descripcion = role[2]

            # Verificar que no exista ya (por si se corre la migración dos veces)
            existing = conn.execute(sa.text(
                "SELECT id FROM roles WHERE nombre = :nombre AND tenant_id = :tid"
            ), {"nombre": nombre, "tid": tenant_id}).fetchone()

            if existing:
                continue

            # Insertar rol clonado
            result = conn.execute(sa.text(
                "INSERT INTO roles (nombre, descripcion, tenant_id) "
                "VALUES (:nombre, :descripcion, :tid) RETURNING id"
            ), {"nombre": nombre, "descripcion": descripcion, "tid": tenant_id})
            new_role_id = result.fetchone()[0]

            # Copiar permisos de menú del rol original
            menu_items = conn.execute(sa.text(
                "SELECT menu_item_id FROM role_menu_permissions WHERE role_id = :rid"
            ), {"rid": old_role_id}).fetchall()

            for item in menu_items:
                conn.execute(sa.text(
                    "INSERT INTO role_menu_permissions (role_id, menu_item_id) "
                    "VALUES (:rid, :mid)"
                ), {"rid": new_role_id, "mid": item[0]})

    # 6. Hacer la columna NOT NULL
    op.alter_column('roles', 'tenant_id', nullable=False)

    # 7. Agregar unique constraint por tenant+nombre
    op.create_unique_constraint('uq_role_tenant_nombre', 'roles', ['tenant_id', 'nombre'])

    # 8. Crear índice en tenant_id
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'])


def downgrade() -> None:
    # Revertir: eliminar columna tenant_id y restaurar unique en nombre
    # ADVERTENCIA: esto elimina los roles duplicados (clonados) y puede
    # dejar inconsistencias si hay usuarios referenciando esos roles.
    op.drop_index('ix_roles_tenant_id', table_name='roles')
    op.drop_constraint('uq_role_tenant_nombre', 'roles', type_='unique')
    op.drop_constraint('fk_roles_tenant_id', 'roles', type_='foreignkey')
    op.drop_column('roles', 'tenant_id')
    op.create_unique_constraint('roles_nombre_key', 'roles', ['nombre'])
