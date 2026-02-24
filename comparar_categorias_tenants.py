import requests
import json

# Autenticación
API_URL = "https://api.masasestacion.cl"
login_data = {"username": "admin@fme.cl", "password": "admin"}
resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("=" * 80)
print("COMPARACIÓN DE CATEGORÍAS POR TENANT")
print("=" * 80)

for tenant_id in [1, 2]:
    resp = requests.get(f"{API_URL}/api/maestras/categorias", headers=headers, params={'tenant_id': tenant_id})
    
    if resp.status_code == 200:
        categorias = resp.json()
        tenant_name = "Masas Estación" if tenant_id == 1 else "El Olivo"
        print(f"\nTenant {tenant_id} ({tenant_name}): {len(categorias)} categorías")
        for c in categorias:
            print(f"  ID {c['id']:>3}: {c['codigo']:<15} - {c['nombre']}")
    else:
        print(f"\n❌ Error obteniendo categorías del tenant {tenant_id}")

print("=" * 80)
