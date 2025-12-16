"""
Script para agregar el menú de Compras al sistema
Ejecutar: docker compose exec backend python add_compras_menu.py
"""
from database.database import SessionLocal
from database import models

def add_compras_menu():
    db = SessionLocal()
    try:
        # 1. Verificar si ya existe el menú de Compras
        existing = db.query(models.MenuItem).filter(models.MenuItem.href == "/admin/compras").first()
        if existing:
            print("✅ El menú de Compras ya existe")
            return
        
        # 2. Crear el nuevo ítem de menú
        compras_menu = models.MenuItem(
            nombre="Compras",
            href="/admin/compras",
            icon="🛒",
            orden=4  # Después de Producción
        )
        db.add(compras_menu)
        db.flush()
        
        print(f"✅ Menú 'Compras' creado con ID: {compras_menu.id}")
        
        # 3. Asignar a rol Admin (asumiendo que Admin tiene ID 1)
        admin_role = db.query(models.Role).filter(models.Role.nombre == "Admin").first()
        if admin_role:
            # Verificar si ya está asignado
            already_assigned = db.execute(
                models.role_menu_permissions.select().where(
                    models.role_menu_permissions.c.role_id == admin_role.id,
                    models.role_menu_permissions.c.menu_item_id == compras_menu.id
                )
            ).first()
            
            if not already_assigned:
                db.execute(
                    models.role_menu_permissions.insert().values(
                        role_id=admin_role.id,
                        menu_item_id=compras_menu.id
                    )
                )
                print(f"✅ Menú asignado al rol '{admin_role.nombre}'")
            else:
                print(f"ℹ️  Menú ya estaba asignado al rol '{admin_role.nombre}'")
        else:
            print("⚠️  Rol 'Admin' no encontrado. Asigna manualmente el menú.")
        
        db.commit()
        print("\n" + "="*60)
        print("✅ MENÚ DE COMPRAS AGREGADO EXITOSAMENTE")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_compras_menu()
