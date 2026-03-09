"""
Script para agregar el menú de Facturas al sistema.
Ejecutar localmente:  .\\venv\\Scripts\\python.exe add_facturas_menu.py
Ejecutar en Docker:   docker compose exec backend python add_facturas_menu.py
"""
from database.database import SessionLocal
from database import models


def add_facturas_menu():
    db = SessionLocal()
    try:
        # 1. Verificar si ya existe
        existing = db.query(models.MenuItem).filter(
            models.MenuItem.href == "/admin/facturas"
        ).first()
        if existing:
            print("✅ El menú de Facturas ya existe")
            return

        # 2. Determinar orden (poner después de Pedidos)
        pedidos_menu = db.query(models.MenuItem).filter(
            models.MenuItem.href == "/admin/pedidos"
        ).first()
        orden = (pedidos_menu.orden + 1) if pedidos_menu else 99

        # 3. Crear el ítem
        facturas_menu = models.MenuItem(
            nombre="Facturas",
            href="/admin/facturas",
            icon="📄",
            orden=orden,
        )
        db.add(facturas_menu)
        db.flush()
        print(f"✅ Menú 'Facturas' creado con ID: {facturas_menu.id}")

        # 4. Asignar a todos los roles que tienen acceso a Pedidos
        roles_con_pedidos = []
        if pedidos_menu:
            roles_con_pedidos = pedidos_menu.roles

        if roles_con_pedidos:
            for role in roles_con_pedidos:
                already_assigned = db.execute(
                    models.role_menu_permissions.select().where(
                        models.role_menu_permissions.c.role_id == role.id,
                        models.role_menu_permissions.c.menu_item_id == facturas_menu.id,
                    )
                ).first()
                if not already_assigned:
                    db.execute(
                        models.role_menu_permissions.insert().values(
                            role_id=role.id,
                            menu_item_id=facturas_menu.id,
                        )
                    )
                    print(f"✅ Menú asignado al rol '{role.nombre}'")
        else:
            # Fallback: asignar solo al rol Admin
            admin_role = db.query(models.Role).filter(
                models.Role.nombre == "Admin"
            ).first()
            if admin_role:
                db.execute(
                    models.role_menu_permissions.insert().values(
                        role_id=admin_role.id,
                        menu_item_id=facturas_menu.id,
                    )
                )
                print(f"✅ Menú asignado al rol '{admin_role.nombre}'")
            else:
                print("⚠️  No se encontró rol Admin. Asigna el menú manualmente.")

        db.commit()
        print("\n" + "=" * 60)
        print("✅ MENÚ DE FACTURAS AGREGADO EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_facturas_menu()
