"""
Script para agregar el menú de Mantenedores (solo para admin).
Ejecutar: python scripts/seed_menu_mantenedores.py
"""
import requests

BASE_URL = "http://localhost:8000"

def setup_menu_mantenedores():
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

    # 4. Verificar si ya existe el menú de Mantenedores
    mantenedores_item = next((m for m in menu_items_actuales if m["nombre"] == "Mantenedores"), None)
    
    if mantenedores_item:
        print(f"ℹ️  El menú 'Mantenedores' ya existe (ID: {mantenedores_item['id']})")
        mantenedores_id = mantenedores_item['id']
    else:
        # 5. Crear el nuevo menu item
        print("➕ Creando menú 'Mantenedores'...")
        nuevo_menu = {
            "nombre": "Mantenedores",
            "href": "/mantenedores",
            "icon": "⚙️",
            "orden": 100  # Al final del menú
        }
        
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code == 201:
            mantenedores_item = resp.json()
            mantenedores_id = mantenedores_item['id']
            print(f"✅ Menú 'Mantenedores' creado (ID: {mantenedores_id})")
        else:
            print(f"❌ Error creando menú: {resp.text}")
            return

    # 6. Asignar el menú solo al rol admin
    print(f"\n🔗 Asignando menú 'Mantenedores' solo al rol admin...")
    
    # Obtener los menu items actuales del admin
    resp = session.get(f"{BASE_URL}/api/admin/roles/{admin_role['id']}/menu", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo menú del admin: {resp.text}")
        return
    
    menu_admin_actual = resp.json()
    menu_ids_admin = [m["id"] for m in menu_admin_actual]
    
    # Agregar Mantenedores si no está
    if mantenedores_id not in menu_ids_admin:
        menu_ids_admin.append(mantenedores_id)
        
        resp = session.put(
            f"{BASE_URL}/api/admin/roles/{admin_role['id']}/menu",
            json=menu_ids_admin,
            headers=headers
        )
        
        if resp.status_code == 204:
            print("✅ Menú 'Mantenedores' asignado al rol admin")
        else:
            print(f"❌ Error asignando menú: {resp.text}")
    else:
        print("ℹ️  El menú 'Mantenedores' ya está asignado al rol admin")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_menu_mantenedores()
