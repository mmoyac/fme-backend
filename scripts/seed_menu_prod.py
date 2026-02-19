"""
Script para poblar el MENÚ en PRODUCCIÓN.
Ejecutar: python scripts/seed_menu_prod.py
"""
import requests
import json
import sys

# URL de producción
BASE_URL = "https://api.masasestacion.cl"

def setup_menu_prod():
    session = requests.Session()

    print(f"🌍 Conectando a {BASE_URL}...")

    # 1. Login
    print(f"🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    try:
        resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Error login: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # ============================================
    # 2. CREAR ITEMS DE MENÚ
    # ============================================
    items_data = [
        { "nombre": "Dashboard", "href": "/admin/dashboard", "icon": "📊", "orden": 1 },
        { "nombre": "Pedidos", "href": "/admin/pedidos", "icon": "🛒", "orden": 2 },
        { "nombre": "POS", "href": "/admin/pedidos/pos", "icon": "💳", "orden": 3 },
        { "nombre": "Productos", "href": "/admin/productos", "icon": "📦", "orden": 4 },
        { "nombre": "Locales", "href": "/admin/locales", "icon": "🏢", "orden": 5 },
        { "nombre": "Inventario", "href": "/admin/inventario", "icon": "📈", "orden": 6 },
        { "nombre": "Precios", "href": "/admin/precios", "icon": "💰", "orden": 7 },
        { "nombre": "Clientes", "href": "/admin/clientes", "icon": "👥", "orden": 8 },
        { "nombre": "Caja", "href": "/admin/caja", "icon": "💵", "orden": 9 },
        { "nombre": "Despacho", "href": "/admin/despacho", "icon": "🚚", "orden": 10 },
        { "nombre": "Transferencias", "href": "/admin/transferencias", "icon": "↔️", "orden": 11 },
        { "nombre": "Compras", "href": "/admin/compras", "icon": "🛍️", "orden": 12 },
        { "nombre": "Recepción", "href": "/admin/recepcion", "icon": "📥", "orden": 13 },
        { "nombre": "Producción", "href": "/admin/produccion", "icon": "🏭", "orden": 14 },
        { "nombre": "Historial", "href": "/admin/historial", "icon": "📋", "orden": 15 },
        { "nombre": "Alertas", "href": "/admin/alertas", "icon": "🔔", "orden": 16 },
        { "nombre": "Mantenedores", "href": "/admin/mantenedores", "icon": "⚙️", "orden": 17 },
        { "nombre": "Usuarios", "href": "/admin/usuarios", "icon": "👤", "orden": 18 },
    ]

    print("--- Creando/Verificando Items de Menú ---")
    
    # Obtener items existentes para no duplicar (aunque el backend debería manejarlo, mejor prevenir)
    existing_items = []
    try:
        resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
        if resp.status_code == 200:
            existing_items = resp.json()
    except:
        pass

    existing_names = {item['nombre']: item for item in existing_items}
    menu_map = {} # Mapa nombre -> ID

    for item_data in items_data:
        if item_data['nombre'] in existing_names:
            print(f"  ℹ️  Item ya existe: {item_data['nombre']}")
            # Actualizar si href/icon cambió (opcional, aquí solo guardamos ID)
            # Podríamos hacer PUT si quisiéramos forzar actualización
            menu_id = existing_names[item_data['nombre']]['id']
            # Actualizar orden/href por si acaso
            update_data = item_data.copy()
            session.put(f"{BASE_URL}/api/admin/menu_items/{menu_id}", json=update_data, headers=headers)
        else:
            resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=item_data, headers=headers)
            if resp.status_code in [200, 201]:
                print(f"  ✅ Creado: {item_data['nombre']}")
                menu_id = resp.json()['id']
            else:
                print(f"  ❌ Error creando {item_data['nombre']}: {resp.text}")
                continue
        
        menu_map[item_data['nombre']] = menu_id

    # ============================================
    # 3. ASIGNAR PERMISOS A ROLES
    # ============================================
    print("\n--- Asignando Permisos a Roles ---")

    # Obtener roles
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    roles = resp.json()
    role_map = {r['nombre']: r['id'] for r in roles}

    roles_config = {
        "admin": list(menu_map.keys()), # Todos
        "administrador": list(menu_map.keys()), # Todos
        "vendedor": ["Dashboard", "Pedidos", "POS", "Productos", "Inventario", "Clientes", "Caja", "Despacho"],
        "tesorero": ["Dashboard", "Pedidos", "Precios", "Clientes", "Caja"],
        "bodeguero": ["Dashboard", "Inventario", "Transferencias", "Recepción", "Productos"],
        "despachador": ["Dashboard", "Despacho", "Pedidos"],
    }

    for role_name, menu_names in roles_config.items():
        if role_name not in role_map:
            print(f"⚠️ Rol '{role_name}' no encontrado en BD")
            continue
        
        role_id = role_map[role_name]
        menu_ids = []
        for name in menu_names:
            if name in menu_map:
                menu_ids.append(menu_map[name])
            else:
                print(f"  ⚠️ Menú '{name}' no encontrado en mapa")

        # Asignar
        resp = session.put(
            f"{BASE_URL}/api/admin/roles/{role_id}/menu",
            json=menu_ids,
            headers=headers
        )
        if resp.status_code == 204:
            print(f"✅ Rol '{role_name}': Asignados {len(menu_ids)} items")
        else:
            print(f"❌ Error asignando a '{role_name}': {resp.text}")

    print("\n✅ Proceso de menú completado!")

if __name__ == "__main__":
    setup_menu_prod()
