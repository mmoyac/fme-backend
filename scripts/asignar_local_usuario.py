"""
Script para asignar un local por defecto a un usuario.
Ejecutar: docker-compose exec backend python scripts/asignar_local_usuario.py
"""
import requests

BASE_URL = "http://localhost:8000"

def asignar_local_usuario():
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

    # 2. Obtener todos los usuarios
    print("👥 Obteniendo usuarios...")
    resp = session.get(f"{BASE_URL}/api/admin/users", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo usuarios: {resp.text}")
        return
    
    usuarios = resp.json()
    print(f"👥 Usuarios encontrados: {len(usuarios)}")
    for user in usuarios:
        print(f"   • {user['email']} (ID: {user['id']}) - Local actual: {user.get('local_defecto_id', 'Sin asignar')}")

    # 3. Obtener todos los locales
    print("\n🏪 Obteniendo locales...")
    resp = session.get(f"{BASE_URL}/api/locales/", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error obteniendo locales: {resp.text}")
        return
    
    locales = resp.json()
    print(f"🏪 Locales encontrados: {len(locales)}")
    for local in locales:
        if local['codigo'] != 'WEB':  # Excluir el local virtual WEB
            print(f"   • {local['nombre']} (ID: {local['id']}) - Código: {local['codigo']}")

    # 4. Asignar el primer local físico al admin
    admin_user = next((u for u in usuarios if u['email'] == 'admin@fme.cl'), None)
    local_fisico = next((l for l in locales if l['codigo'] != 'WEB'), None)
    
    if admin_user and local_fisico:
        print(f"\n🔗 Asignando local '{local_fisico['nombre']}' al usuario admin...")
        
        update_data = {
            "local_defecto_id": local_fisico['id']
        }
        
        resp = session.put(f"{BASE_URL}/api/admin/users/{admin_user['id']}", 
                          json=update_data, headers=headers)
        
        if resp.status_code == 200:
            print(f"✅ Local asignado exitosamente")
            print(f"   • Usuario: {admin_user['email']}")
            print(f"   • Local: {local_fisico['nombre']} (ID: {local_fisico['id']})")
        else:
            print(f"❌ Error asignando local: {resp.text}")
    else:
        if not admin_user:
            print("❌ Usuario admin no encontrado")
        if not local_fisico:
            print("❌ No hay locales físicos disponibles")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    asignar_local_usuario()