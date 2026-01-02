"""
Script para agregar el menú de Caja al sistema.
Ejecutar: docker-compose exec backend python scripts/seed_menu_caja.py
"""
import requests

BASE_URL = "http://localhost:8000"

def setup_menu_caja():
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

    # 4. Verificar si ya existe el menú de Caja
    caja_item = next((m for m in menu_items_actuales if m["nombre"] == "Caja"), None)
    
    if caja_item:
        print(f"ℹ️  El menú 'Caja' ya existe (ID: {caja_item['id']})")
        caja_id = caja_item['id']
    else:
        # 5. Crear el nuevo menu item
        print("➕ Creando menú 'Caja'...")
        nuevo_menu = {
            "nombre": "Caja",
            "href": "/admin/caja",
            "icon": "💰",
            "orden": 50  # Después de Inventario (orden 5) y antes de otros items
        }
        
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code == 201:
            caja_item = resp.json()
            caja_id = caja_item['id']
            print(f"✅ Menú 'Caja' creado (ID: {caja_id})")
        else:
            print(f"❌ Error creando menú: {resp.text}")
            return

    # 6. Asignar el menú a los roles apropiados
    print(f"\n🔗 Asignando menú 'Caja' a roles relevantes...")
    
    # Obtener roles vendedor y admin para asignar Caja
    roles_con_caja = ["admin", "administrador", "vendedor"]
    
    for role_name in roles_con_caja:
        role = next((r for r in roles if r["nombre"] == role_name), None)
        if not role:
            print(f"⚠️ Rol '{role_name}' no encontrado, saltando...")
            continue
            
        # Obtener los menu items actuales del rol
        resp = session.get(f"{BASE_URL}/api/admin/roles/{role['id']}/menu", headers=headers)
        if resp.status_code != 200:
            print(f"❌ Error obteniendo menú del rol {role_name}: {resp.text}")
            continue
        
        menu_role_actual = resp.json()
        menu_ids_role = [m["id"] for m in menu_role_actual]
        
        # Agregar Caja si no está
        if caja_id not in menu_ids_role:
            menu_ids_role.append(caja_id)
            
            resp = session.put(
                f"{BASE_URL}/api/admin/roles/{role['id']}/menu",
                json=menu_ids_role,
                headers=headers
            )
            
            if resp.status_code == 204:
                print(f"✅ Menú 'Caja' asignado al rol {role_name}")
            else:
                print(f"❌ Error asignando menú al rol {role_name}: {resp.text}")
        else:
            print(f"ℹ️  El menú 'Caja' ya está asignado al rol {role_name}")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_menu_caja()