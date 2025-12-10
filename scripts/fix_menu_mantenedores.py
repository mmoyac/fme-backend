"""
Script para corregir el href del menú Mantenedores.
Ejecutar: python scripts/fix_menu_mantenedores.py
"""
import requests

BASE_URL = "http://localhost:8000"

def fix_menu():
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
    resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo menu items: {resp.text}")
        return
    
    menu_items = resp.json()
    
    # 3. Buscar el menú Mantenedores
    mantenedores = next((m for m in menu_items if m["nombre"] == "Mantenedores"), None)
    
    if not mantenedores:
        print("❌ Menú Mantenedores no encontrado")
        return
    
    print(f"📋 Menú encontrado:")
    print(f"   ID: {mantenedores['id']}")
    print(f"   Nombre: {mantenedores['nombre']}")
    print(f"   Href actual: {mantenedores['href']}")
    
    if mantenedores['href'] == '/admin/mantenedores':
        print("\n✅ El href ya está correcto!")
        return
    
    # 4. Actualizar el href
    print(f"\n🔧 Corrigiendo href a '/admin/mantenedores'...")
    
    update_data = {
        "nombre": mantenedores["nombre"],
        "href": "/admin/mantenedores",
        "icon": mantenedores["icon"],
        "orden": mantenedores["orden"]
    }
    
    resp = session.put(
        f"{BASE_URL}/api/admin/menu_items/{mantenedores['id']}",
        json=update_data,
        headers=headers
    )
    
    if resp.status_code == 200:
        print("✅ Href actualizado correctamente!")
        print("\n🔄 Recarga el navegador para ver los cambios.")
    else:
        print(f"❌ Error actualizando: {resp.text}")


if __name__ == "__main__":
    fix_menu()
