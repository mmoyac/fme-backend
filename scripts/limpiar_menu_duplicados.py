"""
Script para limpiar el menú eliminando items duplicados.
Ejecutar: docker-compose exec backend python scripts/limpiar_menu_duplicados.py
"""
import requests

BASE_URL = "http://localhost:8000"

def limpiar_menu_duplicados():
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

    # 2. Obtener todos los menu items
    print("📋 Obteniendo menu items actuales...")
    resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo menu items: {resp.text}")
        return
    
    menu_items = resp.json()

    # 3. Buscar el menú "Resumen de Cajas"
    resumen_cajas = next((m for m in menu_items if m["nombre"] == "Resumen de Cajas"), None)
    
    if resumen_cajas:
        print(f"🗑️  Eliminando menú duplicado 'Resumen de Cajas' (ID: {resumen_cajas['id']})...")
        
        # Eliminar el menu item
        resp = session.delete(f"{BASE_URL}/api/admin/menu_items/{resumen_cajas['id']}", headers=headers)
        
        if resp.status_code == 204:
            print(f"✅ Menú 'Resumen de Cajas' eliminado exitosamente")
        else:
            print(f"❌ Error eliminando menú: {resp.text}")
    else:
        print("ℹ️  No se encontró menú 'Resumen de Cajas' para eliminar")

    print("\n✅ Limpieza completada!")

if __name__ == "__main__":
    limpiar_menu_duplicados()