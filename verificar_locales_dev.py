#!/usr/bin/env python3
"""
Verificar locales en desarrollo
"""
import requests

API_URL = "http://localhost:8000"

# Autenticar
resp = requests.post(
    f"{API_URL}/api/auth/token",
    data={"username": "admin@elolivo.cl", "password": "admin"}
)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Obtener todos los locales
resp = requests.get(f"{API_URL}/api/locales/", headers=headers)
locales = resp.json()

print("📍 LOCALES EN DESARROLLO:")
print("=" * 80)

if not locales:
    print("❌ No hay locales en el sistema")
else:
    for local in locales:
        print(f"ID: {local['id']:3d} | Tenant ID: {local.get('tenant_id', 'N/A'):3s} | Código: {local['codigo']:10s} | Nombre: {local['nombre']}")

print("=" * 80)
print(f"Total: {len(locales)} locales")
