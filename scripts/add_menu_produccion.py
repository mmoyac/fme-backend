
import sys
import os

# Add parent dir to path to import database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models import MenuItem, Role

def add_menu_produccion():
    db = SessionLocal()
    try:
        # 1. Crear/Buscar Menu Item
        menu_prod = db.query(MenuItem).filter(MenuItem.href == "/admin/produccion").first()
        if not menu_prod:
            menu_prod = MenuItem(
                nombre="Producción",
                href="/admin/produccion",
                icon="🏭",
                orden=50 # Ajustar según donde queramos que aparezca
            )
            db.add(menu_prod)
            db.commit()
            print("Menu item 'Producción' creado.")
        else:
            print("Menu item 'Producción' ya existe.")
            
        # 2. Asignar a Rol Admin
        admin_role = db.query(Role).filter(Role.nombre == "admin").first()
        if admin_role:
            if menu_prod not in admin_role.menus:
                admin_role.menus.append(menu_prod)
                db.commit()
                print("Asignado a rol Admin.")
            else:
                print("Ya estaba asignado a Admin.")
        else:
            print("Rol Admin no encontrado!")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_menu_produccion()
