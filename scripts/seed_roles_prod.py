"""
Script para crear ROLES en PRODUCCIÓN.
Ejecutar: python scripts/seed_roles_prod.py
"""
import requests
import json
import sys

# URL de producción
BASE_URL = "https://api.masasestacion.cl"

def setup_roles_prod():
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
    # 2. CREAR ROLES
    # ============================================
    roles_data = [
        {"nombre": "vendedor", "descripcion": "Vendedor de local"},
        {"nombre": "tesorero", "descripcion": "Encargado de finanzas y precios"},
        {"nombre": "bodeguero", "descripcion": "Encargado de inventario"},
    ]

    print("--- Creando Roles ---")
    
    for role in roles_data:
        resp = session.post(f"{BASE_URL}/api/admin/roles", json=role, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Creado: {role['nombre']}")
        elif resp.status_code == 400:
            print(f"  ℹ️  Ya existe: {role['nombre']}")
        else:
            print(f"  ❌ Error creando {role['nombre']}: {resp.text}")

    print("\n✅ Roles creados!")

if __name__ == "__main__":
    setup_roles_prod()
