"""
Script para agregar el menú de Configuración Landing (solo para admin).
Ejecutar: python scripts/seed_menu_config_landing.py
"""
import requests

BASE_URL = "http://localhost:8000"

def setup_menu_config_landing():
    session = requests.Session()

    # 1. Login
    print(f"🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error login: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # 2. Obtener el rol admin
    print("📋 Obteniendo rol admin...")
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo roles: {resp.text}")
        return
    
    roles = resp.json()
    admin_role = next((r for r in roles if r["nombre"] == "admin"), None)
    if not admin_role:
        print("❌ Rol admin no encontrado")
        return
    
    print(f"✅ Rol admin encontrado (ID: {admin_role['id']})\n")

    # 3. Obtener todos los menu items actuales
    resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo menu items: {resp.text}")
        return
    
    menu_items_actuales = resp.json()
    print(f"📋 Menu items actuales: {len(menu_items_actuales)}")

    # 4. Verificar si ya existe el menú de Configuración Landing
    config_landing_item = next((m for m in menu_items_actuales if m["nombre"] == "Config. Landing"), None)
    
    if config_landing_item:
        print(f"ℹ️  El menú 'Config. Landing' ya existe (ID: {config_landing_item['id']})")
        config_landing_id = config_landing_item['id']
    else:
        # 5. Crear el nuevo menu item
        print("➕ Creando menú 'Config. Landing'...")
        nuevo_menu = {
            "nombre": "Config. Landing",
            "href": "/admin/configuracion/landing",
            "icon": "🌐",
            "orden": 101  # Justo después de Mantenedores (100)
        }
        
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code == 201:
            config_landing_item = resp.json()
            config_landing_id = config_landing_item['id']
            print(f"✅ Menú 'Config. Landing' creado (ID: {config_landing_id})")
        else:
            print(f"❌ Error creando menú: {resp.text}")
            return

    # 6. Asignar el menú solo al rol admin
    print(f"\n🔗 Asignando menú 'Config. Landing' solo al rol admin...")
    
    # Obtener los menu items actuales del admin
    resp = session.get(f"{BASE_URL}/api/admin/roles/{admin_role['id']}/menu", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo menú del admin: {resp.text}")
        return
    
    menu_admin_actual = resp.json()
    menu_ids_admin = [m["id"] for m in menu_admin_actual]
    
    # Agregar Config. Landing si no está
    if config_landing_id not in menu_ids_admin:
        menu_ids_admin.append(config_landing_id)
        
        resp = session.put(
            f"{BASE_URL}/api/admin/roles/{admin_role['id']}/menu",
            json=menu_ids_admin,
            headers=headers
        )
        
        if resp.status_code == 204:
            print("✅ Menú 'Config. Landing' asignado al rol admin")
        else:
            print(f"❌ Error asignando menú: {resp.text}")
            return
    else:
        print("ℹ️  El menú 'Config. Landing' ya está asignado al admin")

    print("\n✅ ¡Configuración completada!")
    print(f"🌐 Ahora los administradores verán 'Config. Landing' en el sidebar")

if __name__ == "__main__":
    setup_menu_config_landing()
