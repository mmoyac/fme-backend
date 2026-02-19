#!/usr/bin/env python3
"""
Verificar producto recién creado
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

# Obtener producto ID 48
resp = requests.get(f"{API_URL}/api/productos/48", headers=headers)
if resp.status_code == 200:
    producto = resp.json()
    print("📦 PRODUCTO ID 48:")
    print("=" * 80)
    print(f"SKU: {producto.get('sku')}")
    print(f"Nombre: {producto.get('nombre')}")
    print(f"Tenant ID: {producto.get('tenant_id')}")
    print(f"Unidad Medida ID: {producto.get('unidad_medida_id')}")
    print(f"Categoría ID: {producto.get('categoria_id')}")
    print(f"Tipo Producto ID: {producto.get('tipo_producto_id')}")
    print("=" * 80)
else:
    print(f"❌ Error: {resp.status_code} - {resp.text}")
