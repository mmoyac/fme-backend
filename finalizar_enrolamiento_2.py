#!/usr/bin/env python3
"""
Script para finalizar el enrolamiento 2 manualmente
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Función para autenticarse
def login():
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"Error en login: {response.status_code}")
        print(response.text)
        return None

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def main():
    print("🔐 Obteniendo token de acceso...")
    token = login()
    if not token:
        print("❌ No se pudo autenticar")
        return
    
    headers = get_headers(token)
    
    # Intentar finalizar enrolamiento 2
    enrolamiento_id = 2
    print(f"\n🚀 Intentando finalizar enrolamiento {enrolamiento_id}...")
    
    update_data = {
        "estado_id": 3  # FINALIZADO
    }
    
    response = requests.put(
        f"{BASE_URL}/api/enrolamiento/enrolamientos/{enrolamiento_id}",
        json=update_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Enrolamiento finalizado exitosamente!")
        result = response.json()
        print(f"Estado actual: {result['estado']['nombre']}")
    else:
        print(f"❌ Error finalizando enrolamiento: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()