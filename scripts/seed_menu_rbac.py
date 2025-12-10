
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Role, MenuItem
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = "postgresql://fme:fme@db:5432/fme_database"

def seed_menu():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Definir Items de Menu
        items_data = [
            { "nombre": "Dashboard", "href": "/admin/dashboard", "icon": "📊", "orden": 1 },
            { "nombre": "Pedidos", "href": "/admin/pedidos", "icon": "🛒", "orden": 2 },
            { "nombre": "Productos", "href": "/admin/productos", "icon": "📦", "orden": 3 },
            { "nombre": "Locales", "href": "/admin/locales", "icon": "🏢", "orden": 4 },
            { "nombre": "Inventario", "href": "/admin/inventario", "icon": "📈", "orden": 5 },
            { "nombre": "Precios", "href": "/admin/precios", "icon": "💰", "orden": 6 },
            { "nombre": "Clientes", "href": "/admin/clientes", "icon": "👥", "orden": 7 },
            { "nombre": "Transferencias", "href": "/admin/transferencias", "icon": "↔️", "orden": 8 },
            { "nombre": "Historial", "href": "/admin/historial", "icon": "📋", "orden": 9 },
            { "nombre": "Usuarios", "href": "/admin/usuarios", "icon": "👤", "orden": 10 },
        ]

        menu_map = {}

        print("--- Creando Items de Menú ---")
        for i_data in items_data:
            item = db.query(MenuItem).filter(MenuItem.nombre == i_data["nombre"]).first()
            if not item:
                item = MenuItem(**i_data)
                db.add(item)
                db.commit()
                db.refresh(item)
                print(f"Creado: {item.nombre}")
            else:
                # Update href/icon/orden if changed
                item.href = i_data["href"]
                item.icon = i_data["icon"]
                item.orden = i_data["orden"]
                db.commit()
                print(f"Actualizado: {item.nombre}")
            menu_map[item.nombre] = item

        # 2. Configurar Roles
        print("\n--- Asignando Permisos ---")
        
        roles_config = {
            "admin": "ALL",
            "administrador": "ALL",
            "vendedor": ["Dashboard", "Pedidos", "Productos", "Inventario", "Clientes", "Transferencias"],
            "tesorero": ["Dashboard", "Pedidos", "Precios", "Clientes"],
        }
        
        all_menus = list(menu_map.values())
        
        for role_name, permissions in roles_config.items():
            role = db.query(Role).filter(Role.nombre == role_name).first()
            if not role:
                print(f"⚠️ Rol no encontrado: {role_name}")
                continue
            
            # Limpiar permisos actuales (para resetear)
            role.menus = []
            
            if permissions == "ALL":
                role.menus = all_menus
                print(f"✅ {role_name}: Acceso TOTAL ({len(role.menus)} items)")
            else:
                selected_menus = [menu_map[p] for p in permissions if p in menu_map]
                role.menus = selected_menus
                print(f"✅ {role_name}: Acceso a {len(role.menus)} items")
            
            db.commit()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_menu()
