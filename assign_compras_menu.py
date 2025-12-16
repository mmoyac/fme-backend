"""
Script para asignar el menú de Compras a todos los roles
"""
from database.database import SessionLocal
from database import models

def assign_compras_to_roles():
    db = SessionLocal()
    try:
        # Buscar el menú de Compras
        compras_menu = db.query(models.MenuItem).filter(models.MenuItem.href == "/admin/compras").first()
        if not compras_menu:
            print("❌ Menú de Compras no encontrado")
            return
        
        print(f"✅ Menú encontrado: {compras_menu.nombre} (ID: {compras_menu.id})")
        
        # Listar todos los roles
        roles = db.query(models.Role).all()
        print(f"\n📋 Roles disponibles:")
        for role in roles:
            print(f"   - {role.nombre} (ID: {role.id})")
        
        # Asignar a todos los roles
        for role in roles:
            # Verificar si ya está asignado
            already_assigned = db.execute(
                models.role_menu_permissions.select().where(
                    models.role_menu_permissions.c.role_id == role.id,
                    models.role_menu_permissions.c.menu_item_id == compras_menu.id
                )
            ).first()
            
            if not already_assigned:
                db.execute(
                    models.role_menu_permissions.insert().values(
                        role_id=role.id,
                        menu_item_id=compras_menu.id
                    )
                )
                print(f"   ✅ Asignado a '{role.nombre}'")
            else:
                print(f"   ℹ️  Ya estaba asignado a '{role.nombre}'")
        
        db.commit()
        print("\n" + "="*60)
        print("✅ MENÚ ASIGNADO A TODOS LOS ROLES")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    assign_compras_to_roles()
