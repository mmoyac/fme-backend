
import requests
import json

BASE_URL = "http://localhost:8000"

def setup_demo_data():
    session = requests.Session()

    # 1. Login
    print(f"Logueando como admin...")
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
    print("✅ Login exitoso")

    # 2. Crear Roles
    roles_to_create = [
        {"nombre": "administrador", "descripcion": "Dueño del negocio"},
        {"nombre": "tesorero", "descripcion": "Encargado de finanzas"},
        {"nombre": "vendedor", "descripcion": "Encargado de ventas"}
    ]

    for role in roles_to_create:
        resp = session.post(f"{BASE_URL}/api/admin/roles", json=role, headers=headers)
        if resp.status_code == 201:
            print(f"✅ Rol creado: {role['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"ℹ️  Rol ya existe: {role['nombre']}")
        else:
            print(f"❌ Error creando rol {role['nombre']}: {resp.text}")

    # 3. Obtener Roles para tener IDs
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    if resp.status_code != 200:
        print("❌ Error obteniendo roles")
        return
    
    roles_map = {r["nombre"]: r["id"] for r in resp.json()}
    print(f"📋 Mapa de Roles: {roles_map}")

    # 4. Crear Usuarios
    users_to_create = [
        {
            "email": "cliente@fme.cl",
            "password": "admin",
            "nombre_completo": "Cliente Dueño",
            "role_id": roles_map.get("administrador"),
            "is_active": True
        },
        {
            "email": "tesorero@fme.cl",
            "password": "admin",
            "nombre_completo": "Juan Tesorero",
            "role_id": roles_map.get("tesorero"),
            "is_active": True
        },
        {
            "email": "vendedor@fme.cl",
            "password": "admin",
            "nombre_completo": "Ana Vendedora",
            "role_id": roles_map.get("vendedor"),
            "is_active": True
        }
    ]

    for user in users_to_create:
        if not user["role_id"]:
            print(f"⚠️ Saltando usuario {user['email']} por falta de ID de rol")
            continue

        resp = session.post(f"{BASE_URL}/api/admin/users", json=user, headers=headers)
        if resp.status_code == 201:
            print(f"✅ Usuario creado: {user['email']}")
        elif resp.status_code == 400 and "registrado" in resp.text:
            print(f"ℹ️  Usuario ya existe: {user['email']}")
        else:
            print(f"❌ Error creando usuario {user['email']}: {resp.text}")

if __name__ == "__main__":
    setup_demo_data()
