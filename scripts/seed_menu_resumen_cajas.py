"""
Script para agregar el menú de Resumen de Cajas al sistema.
Ejecutar: docker-compose exec backend python scripts/seed_menu_resumen_cajas.py
"""
import requests

BASE_URL = "http://localhost:8000"

def setup_menu_resumen_cajas():
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

    # 4. Verificar si ya existe el menú de Resumen de Cajas
    resumen_item = next((m for m in menu_items_actuales if m["nombre"] == "Resumen de Cajas"), None)
    
    if resumen_item:
        print(f"ℹ️  El menú 'Resumen de Cajas' ya existe (ID: {resumen_item['id']})")
        resumen_id = resumen_item['id']
    else:
        # 5. Crear el nuevo menu item
        print("➕ Creando menú 'Resumen de Cajas'...")
        nuevo_menu = {
            "nombre": "Resumen de Cajas",
            "href": "/admin/resumen-cajas",
            "icon": "📊",
            "orden": 51  # Después de Caja (orden 50)
        }
        
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code == 201:
            resumen_item = resp.json()
            resumen_id = resumen_item['id']
            print(f"✅ Menú 'Resumen de Cajas' creado (ID: {resumen_id})")
        else:
            print(f"❌ Error creando menú: {resp.text}")
            return

    # 6. Asignar el menú a los roles apropiados (solo admin/administrador)
    print(f"\n🔗 Asignando menú 'Resumen de Cajas' a roles relevantes...")
    
    # Solo roles de gestión/supervisión necesitan ver el resumen de todas las cajas
    roles_con_resumen = ["admin", "administrador"]
    
    for role_name in roles_con_resumen:
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
        
        # Agregar Resumen de Cajas si no está
        if resumen_id not in menu_ids_role:
            menu_ids_role.append(resumen_id)
            
            resp = session.put(
                f"{BASE_URL}/api/admin/roles/{role['id']}/menu",
                json=menu_ids_role,
                headers=headers
            )
            
            if resp.status_code == 204:
                print(f"✅ Menú 'Resumen de Cajas' asignado al rol {role_name}")
            else:
                print(f"❌ Error asignando menú al rol {role_name}: {resp.text}")
        else:
            print(f"ℹ️  El menú 'Resumen de Cajas' ya está asignado al rol {role_name}")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_menu_resumen_cajas()