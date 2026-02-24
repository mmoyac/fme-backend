import requests
import json

# Autenticación
API_URL = "https://api.masasestacion.cl"
login_data = {"username": "admin@fme.cl", "password": "admin"}
resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Obtener categorías
resp = requests.get(f"{API_URL}/api/maestras/categorias", headers=headers, params={'tenant_id': 1})

print("=" * 80)
print(f"Status Code: {resp.status_code}")
print("=" * 80)

if resp.status_code == 200:
    categorias = resp.json()
    print(f"Total categorías: {len(categorias)}\n")
    for c in categorias:
        print(f"  ID {c['id']:>3}: {c['nombre']}")
    print("=" * 80)
else:
    print("Response:")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
