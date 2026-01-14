"""
Script para agregar el menú de Alertas.
Ejecutar: python scripts/add_menu_alertas.py
"""
import requests

BASE_URL = "http://localhost:8000"

def add_menu_alertas():
    session = requests.Session()

    # 1. Login como admin
    print("🔐 Logueando como admin...")
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

    # 2. Obtener roles
    print("👥 Obteniendo roles...")
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

    # 4. Verificar si ya existe el menú de Alertas
    alertas_item = next((m for m in menu_items_actuales if m["nombre"] == "Alertas"), None)
    
    if alertas_item:
        print(f"ℹ️  El menú 'Alertas' ya existe (ID: {alertas_item['id']})")
        alertas_id = alertas_item['id']
    else:
        # 5. Crear el nuevo menu item
        print("➕ Creando menú 'Alertas'...")
        nuevo_menu = {
            "nombre": "Alertas",
            "href": "/admin/alertas",
            "icon": "⚠️",
            "orden": 12  # Después de Mantenedores
        }
        
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code == 201:
            alertas_item = resp.json()
            alertas_id = alertas_item['id']
            print(f"✅ Menú 'Alertas' creado (ID: {alertas_id})")
        else:
            print(f"❌ Error creando menú: {resp.text}")
            return

    # 6. Asignar el menú a los roles apropiados
    print(f"\n🔗 Asignando menú 'Alertas' a roles relevantes...")
    
    # Solo admin puede ver alertas
    roles_con_alertas = ["admin", "administrador"]
    
    for role_name in roles_con_alertas:
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
        
        # Agregar Alertas si no está
        if alertas_id not in menu_ids_role:
            menu_ids_role.append(alertas_id)
            
            # Actualizar el menú del rol
            resp = session.put(f"{BASE_URL}/api/admin/roles/{role['id']}/menu", 
                             json=menu_ids_role, headers=headers)
            if resp.status_code in [200, 204]:
                print(f"✅ Alertas asignado al rol '{role_name}'")
            else:
                print(f"❌ Error asignando a '{role_name}': {resp.text}")
        else:
            print(f"ℹ️  Rol '{role_name}' ya tiene acceso a Alertas")

    print("\n✅ Configuración de menú de Alertas completada!")
    print("🔄 Nota: Los usuarios deben volver a cargar la página para ver el nuevo menú.")

if __name__ == "__main__":
    add_menu_alertas()