"""
Eliminar producto 999999 (ID: 22) de producción.
"""
import requests

API_URL = "https://api.masasestacion.cl"

# Autenticar
resp = requests.post(f"{API_URL}/api/auth/token", data={
    "username": "admin@fme.cl",
    "password": "admin"
})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Eliminar producto
print("🗑️  Eliminando producto SKU 999999 (ID: 22)...")
resp = requests.delete(f"{API_URL}/api/productos/22", headers=headers)

if resp.status_code in [200, 204]:
    print("✅ Producto eliminado exitosamente")
else:
    print(f"❌ ERROR: {resp.status_code} - {resp.text}")
