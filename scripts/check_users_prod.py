"""
Script para listar usuarios en producción y verificar si existen.
Ejecutar: python scripts/check_users_prod.py
"""
import requests
import sys

BASE_URL = "https://api.masasestacion.cl"

def check_users():
    session = requests.Session()
    
    # 1. Login Admin
    print(f"🔐 Logueando como admin...")
    login_data = {"username": "admin@fme.cl", "password": "admin"}
    try:
        resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Error login Admin: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error conexión: {e}")
        return
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login Admin exitoso\n")
    
    # 2. Listar Usuarios
    print("📋 Listando usuarios...")
    try:
        resp = session.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if resp.status_code == 200:
            users = resp.json()
            print(f"Total Usuarios: {len(users)}")
            for u in users:
                print(f"  - {u['email']} (Rol: {u['role']['nombre']}) - Activo: {u['is_active']}")
        else:
            print(f"❌ Error listando usuarios: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Error al listar: {e}")

if __name__ == "__main__":
    check_users()
