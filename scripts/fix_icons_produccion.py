import requests
import sys

API_URL = "https://api.masasestacion.cl/api"
EMAIL = "admin@fme.cl"
PASSWORD = "admin"

ICON_MAP = {
    "/admin/dashboard": "📊",
    "/admin/productos": "📦",
    "/admin/locales": "🏪",
    "/admin/inventario": "📋",
    "/admin/compras": "🛒",
    "/admin/produccion": "🏭",
    "/admin/precios": "💲",
    "/admin/mantenedores": "⚙️",
    "/admin/users": "👥"
}

def fix_icons():
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

    # Obtener Items actuales
    print("📦 Obteniendo items de menú...")
    resp = requests.get(f"{API_URL}/admin/menu_items", headers=headers)
    current_items = resp.json()
    
    for item in current_items:
        href = item["href"]
        if href in ICON_MAP:
            new_icon = ICON_MAP[href]
            if item["icon"] != new_icon:
                print(f"🔄 Actualizando icono para {item['nombre']} ({item['icon']} -> {new_icon})...")
                # Update payload. Important: endpoint requires full object usually or at least required fields.
                # MenuItemCreate schema likely requires: nombre, href, icon, orden.
                payload = {
                    "nombre": item["nombre"],
                    "href": item["href"],
                    "icon": new_icon,
                    "orden": item["orden"]
                }
                
                upd_resp = requests.put(f"{API_URL}/admin/menu_items/{item['id']}", json=payload, headers=headers)
                if upd_resp.status_code == 200:
                    print("   OK")
                else:
                    print(f"   ❌ Error: {upd_resp.text}")
            else:
                print(f"✅ {item['nombre']} ya tiene el icono correcto.")
        else:
            print(f"⚠️ Sin mapeo para {item['nombre']} ({href})")

    print("🎉 Iconos actualizados. Refresque la página.")

if __name__ == "__main__":
    fix_icons()
