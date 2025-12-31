#!/usr/bin/env python3
"""
Script para probar los endpoints de stock y precios.
"""
import requests

# Configuración
BASE_URL = "http://localhost:8000"

def login_admin():
    """Login como administrador."""
    print("🔐 Logueando como admin...")
    
    session = requests.Session()
    
    # Datos de login
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error en login: {resp.status_code}")
        return None, None
        
    token_data = resp.json()
    token = token_data.get("access_token")
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso")
    
    return session, headers

def probar_endpoints():
    """Probar los endpoints de stock y precios."""
    session, headers = login_admin()
    if not session:
        return
    
    print("\n📦 Probando endpoint de inventario...")
    print("Producto: Queso (ID=18), Local: Lampa (ID=1)")
    
    # Probar stock
    resp = session.get(f"{BASE_URL}/api/inventario/producto/18/local/1", headers=headers)
    print(f"🔍 Stock response: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Stock: {data.get('cantidad_stock')} unidades")
    else:
        print(f"❌ Error: {resp.text}")
    
    print("\n💰 Probando endpoint de precios...")
    # Probar precio
    resp = session.get(f"{BASE_URL}/api/precios/producto/18/local/1", headers=headers)
    print(f"🔍 Precio response: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Precio: ${data.get('monto_precio')}")
    else:
        print(f"❌ Error: {resp.text}")

if __name__ == "__main__":
    probar_endpoints()