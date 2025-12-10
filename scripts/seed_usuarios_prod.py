"""
Script para crear USUARIOS de prueba en PRODUCCIÓN.
Ejecutar: python scripts/seed_usuarios_prod.py
"""
import requests
import json
import sys

# URL de producción
BASE_URL = "https://api.masasestacion.cl"

def setup_usuarios_prod():
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

    # 2. Obtener Roles para saber IDs
    print("📋 Obteniendo roles...")
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    roles = resp.json()
    role_map = {r['nombre']: r['id'] for r in roles}
    
    # 3. Definir Usuarios
    usuarios = [
        {
            "email": "vendedor@fme.cl",
            "password": "vendedor123",
            "nombre_completo": "Vendedor Estación",
            "role_nombre": "vendedor",
            "is_active": True
        },
        {
            "email": "tesorero@fme.cl",
            "password": "tesorero123",
            "nombre_completo": "Tesorero Principal",
            "role_nombre": "tesorero",
            "is_active": True
        }
    ]

    # Verificar si existe rol cliente, si no, lo intentamos crear o saltar
    # Generalmente los clientes se registran por fuera, pero si quieres un usuario interno...
    if "cliente" in role_map:
         usuarios.append({
            "email": "cliente@fme.cl",
            "password": "cliente123",
            "nombre_completo": "Cliente Prueba",
            "role_nombre": "cliente",
            "is_active": True
        })
    else:
        print("ℹ️  Rol 'cliente' no existe, saltando creación de usuario cliente.")

    print("\n--- Creando Usuarios ---")
    
    for u in usuarios:
        role_name = u.pop("role_nombre")
        if role_name not in role_map:
            print(f"⚠️ Rol '{role_name}' no encontrado, saltando usuario {u['email']}")
            continue
        
        u["role_id"] = role_map[role_name]
        
        # Crear usuario
        resp = session.post(f"{BASE_URL}/api/admin/users", json=u, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Creado: {u['email']} ({role_name})")
        elif resp.status_code == 400 and "registrado" in resp.text:
            print(f"  ℹ️  Ya existe: {u['email']}")
        else:
            print(f"  ❌ Error creando {u['email']}: {resp.text}")

    print("\n✅ Usuarios creados!")

if __name__ == "__main__":
    setup_usuarios_prod()
