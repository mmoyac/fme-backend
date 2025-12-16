"""
Script para poblar TIPOS DE DOCUMENTO.
Ejecutar: python scripts/seed_tipos_documento.py
"""
import requests
import json
import os
import sys

# Agregar el directorio raíz al path para poder importar módulos si fuera necesario, 
# pero aquí usaremos requests directo a la API local.

# URL local por defecto
BASE_URL = "http://localhost:8000"

def setup_tipos_documento():
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

    # 2. Tipos de Documento
    print("📄 Creando Tipos de Documento...")
    tipos = [
        {"codigo": "FAC", "nombre": "Factura Electrónica", "activo": True},
        {"codigo": "BOL", "nombre": "Boleta Electrónica", "activo": True},
        {"codigo": "GUI", "nombre": "Guía de Despacho", "activo": True},
        {"codigo": "NC", "nombre": "Nota de Crédito", "activo": True},
        {"codigo": "ND", "nombre": "Nota de Débito", "activo": True},
    ]

    for tipo in tipos:
        # Check if exists (by code, or just try create and catch 400)
        # The API creation checks for code uniqueness
        resp = session.post(f"{BASE_URL}/api/maestras/tipos-documento", json=tipo, headers=headers)
        if resp.status_code in [200, 201]:
            print(f"  ✅ Creado: {tipo['nombre']}")
        elif resp.status_code == 400:
            print(f"  ℹ️  Ya existe: {tipo['nombre']}")
        elif resp.status_code == 404:
             print(f"  ❌ Endpoint no encontrado. ¿Reiniciaste el backend? {resp.status_code}")
        else:
            print(f"  ❌ Error: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    setup_tipos_documento()
