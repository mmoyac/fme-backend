import requests
import sys

API_URL = "https://api.masasestacion.cl/api"
EMAIL = "admin@fme.cl"
PASSWORD = "admin"

REQUIRED_ITEMS = [
    {"nombre": "Dashboard", "href": "/admin/dashboard", "icon": "LayoutDashboard", "orden": 1},
    {"nombre": "Productos", "href": "/admin/productos", "icon": "Package", "orden": 2},
    {"nombre": "Locales", "href": "/admin/locales", "icon": "Store", "orden": 3},
    {"nombre": "Inventario", "href": "/admin/inventario", "icon": "ClipboardList", "orden": 4},
    {"nombre": "Compras", "href": "/admin/compras", "icon": "ShoppingCart", "orden": 5},
    {"nombre": "Producción", "href": "/admin/produccion", "icon": "Factory", "orden": 6},
    {"nombre": "Precios", "href": "/admin/precios", "icon": "DollarSign", "orden": 7},
    {"nombre": "Mantenedores", "href": "/admin/mantenedores", "icon": "Settings", "orden": 8},
    {"nombre": "Usuarios", "href": "/admin/usuarios", "icon": "Users", "orden": 9},
]

def seed_menu():
    print("🔑 Autenticando...")
    try:
        resp = requests.post(f"{API_URL}/auth/token", data={
            "username": EMAIL, "password": PASSWORD
        })
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Error Login: {resp.status_code}")
        return

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obtener Rol Admin
    resp = requests.get(f"{API_URL}/admin/roles", headers=headers)
    roles = resp.json()
    admin_role = next((r for r in roles if r["nombre"] == "admin"), None)
    if not admin_role:
        print("❌ Rol admin no encontrado")
        return

    # Obtener Items actuales
    print("📦 Analizando menú existente...")
    resp = requests.get(f"{API_URL}/admin/menu_items", headers=headers)
    current_items = resp.json()
    current_hrefs = {item["href"]: item for item in current_items}
    
    final_ids = []
    
    for req in REQUIRED_ITEMS:
        if req["href"] in current_hrefs:
            # Ya existe, guardamos ID
            existing = current_hrefs[req["href"]]
            final_ids.append(existing["id"])
            # Podríamos actualizar nombre/icono si quisiéramos (PUT), pero lo dejaremos así por ahora.
            print(f"✅ Existe: {req['nombre']}")
        else:
            # Crear
            print(f"➕ Creando: {req['nombre']}...")
            resp = requests.post(f"{API_URL}/admin/menu_items", json=req, headers=headers)
            if resp.status_code == 201:
                new_item = resp.json()
                final_ids.append(new_item["id"])
                print("   OK")
            else:
                print(f"   ❌ Falla al crear {req['nombre']}: {resp.text}")

    # Actualizar Rol
    print(f"🚀 Asignando {len(final_ids)} items al rol Admin...")
    resp = requests.put(f"{API_URL}/admin/roles/{admin_role['id']}/menu", json=final_ids, headers=headers)
    
    if resp.status_code in [200, 204]:
        print("🎉 Menú de producción actualizado correctamente!")
    else:
        print(f"❌ Error al asignar menú: {resp.text}")

if __name__ == "__main__":
    seed_menu()
