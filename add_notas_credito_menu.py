"""
Script para agregar el menú de Notas de Crédito al sistema.
Ejecutar localmente:  .\\venv\\Scripts\\python.exe add_notas_credito_menu.py
Ejecutar en Docker:   docker compose exec backend python add_notas_credito_menu.py
"""
from database.database import SessionLocal
from database import models


def add_notas_credito_menu():
    db = SessionLocal()
    try:
        # 1. Verificar si ya existe
        existing = db.query(models.MenuItem).filter(
            models.MenuItem.href == "/admin/notas-credito"
        ).first()
        if existing:
            print("✅ El menú de Notas de Crédito ya existe")
            return

        # 2. Poner después de Facturas
        facturas_menu = db.query(models.MenuItem).filter(
            models.MenuItem.href == "/admin/facturas"
        ).first()
        orden = (facturas_menu.orden + 1) if facturas_menu else 99

        # 3. Crear el ítem
        notas_menu = models.MenuItem(
            nombre="Notas de Crédito",
            href="/admin/notas-credito",
            icon="🧾",
            orden=orden,
        )
        db.add(notas_menu)
        db.flush()
        print(f"✅ Menú 'Notas de Crédito' creado con ID: {notas_menu.id}")

        # 4. Asignar a los mismos roles que tienen acceso a Facturas
        roles_con_facturas = facturas_menu.roles if facturas_menu else []

        if roles_con_facturas:
            for role in roles_con_facturas:
                already_assigned = db.execute(
                    models.role_menu_permissions.select().where(
                        models.role_menu_permissions.c.role_id == role.id,
                        models.role_menu_permissions.c.menu_item_id == notas_menu.id,
                    )
                ).first()
                if not already_assigned:
                    db.execute(
                        models.role_menu_permissions.insert().values(
                            role_id=role.id,
                            menu_item_id=notas_menu.id,
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
                        menu_item_id=notas_menu.id,
                    )
                )
                print(f"✅ Menú asignado al rol '{admin_role.nombre}'")
            else:
                print("⚠️  No se encontró rol Admin. Asigna el menú manualmente.")

        db.commit()
        print("\n" + "=" * 60)
        print("✅ MENÚ DE NOTAS DE CRÉDITO AGREGADO EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_notas_credito_menu()
