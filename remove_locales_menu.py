"""
Script para eliminar el menú de Locales del sidebar
Ejecutar: docker compose exec backend python remove_locales_menu.py
"""
from database.database import SessionLocal
from database import models

def remove_locales_menu():
    db = SessionLocal()
    try:
        # Buscar el menú de Locales
        locales_menu = db.query(models.MenuItem).filter(models.MenuItem.href == "/admin/locales").first()
        
        if not locales_menu:
            print("ℹ️  El menú de Locales no existe en la base de datos")
            return
        
        print(f"✅ Menú encontrado: {locales_menu.nombre} (ID: {locales_menu.id})")
        
        # Eliminar las asignaciones de roles primero
        db.execute(
            models.role_menu_permissions.delete().where(
                models.role_menu_permissions.c.menu_item_id == locales_menu.id
            )
        )
        print(f"✅ Asignaciones de roles eliminadas")
        
        # Eliminar el menú
        db.delete(locales_menu)
        db.commit()
        
        print("\n" + "="*60)
        print("✅ MENÚ DE LOCALES ELIMINADO DEL SIDEBAR")
        print("="*60)
        print("\nAhora Locales solo está disponible en Mantenedores")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    remove_locales_menu()
