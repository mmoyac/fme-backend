import requests
import sys

API_URL = "https://api.masasestacion.cl/api"
EMAIL = "admin@fme.cl"
PASSWORD = "admin"

def fix_menu():
    print("🔑 Autenticando en PRODUCCIÓN...")
    try:
        resp = requests.post(f"{API_URL}/auth/token", data={
            "username": EMAIL, "password": PASSWORD
        })
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Error Login: {resp.status_code} - {resp.text}")
        print("Si has cambiado la contraseña del admin en producción, este script fallará.")
        return

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Obtener Roles
    print("🔍 Buscando Rol Admin...")
    resp = requests.get(f"{API_URL}/admin/roles", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo roles: {resp.text}")
        return
        
    roles = resp.json()
    admin_role = next((r for r in roles if r["nombre"] == "admin"), None)
    if not admin_role:
        print("❌ Rol admin no encontrado")
        return
    
    print(f"✅ Rol Admin ID: {admin_role['id']}")

    # 3. Listar Items de Menú
    print("📦 Obteniendo items de menú...")
    resp = requests.get(f"{API_URL}/admin/menu_items", headers=headers)
    items = resp.json()
    
    # Filtrar los que queremos MANTENER
    exclude_hrefs = ["/admin/transferencias", "/admin/historial"]
    
    keep_ids = [item["id"] for item in items if item["href"] not in exclude_hrefs]
    removed_items = [item for item in items if item["href"] in exclude_hrefs]
    
    print(f"ℹ️ Total items encontrados: {len(items)}")
    print(f"🗑️ Items a remover del sidebar: {[i['nombre'] for i in removed_items]}")
    
    if not removed_items:
        print("⚠️ No se encontraron los items 'Transferencias' o 'Historial'. Quizás ya fueron borrados.")
        # Igual mandamos el update para asegurar integridad
    
    # 4. Actualizar Menú del Rol
    print(f"🚀 Actualizando menú para usuario Admin...")
    
    resp = requests.put(f"{API_URL}/admin/roles/{admin_role['id']}/menu", json=keep_ids, headers=headers)
    
    if resp.status_code in [200, 204]:
        print("✅ Menú actualizado exitosamente en Producción.")
        print("💡 Nota: El usuario debe volver a iniciar sesión o recargar la página para ver los cambios.")
    else:
        print(f"❌ Error actualizando: {resp.text}")

if __name__ == "__main__":
    fix_menu()
