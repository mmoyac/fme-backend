import requests

# Autenticación
API_URL = "https://api.masasestacion.cl"
login_data = {"username": "admin@fme.cl", "password": "admin"}
resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Obtener productos SIN límite
resp_prod = requests.get(f"{API_URL}/api/productos/", headers=headers, params={'tenant_id': 1, 'limit': 10000})

print("=" * 80)
print(f"Status Code: {resp_prod.status_code}")
print(f"Headers: {dict(resp_prod.headers)}")
print("=" * 80)

productos = resp_prod.json()
print(f"\n📦 TOTAL PRODUCTOS: {len(productos)}")

# Ver si hay algún header de paginación
if 'X-Total-Count' in resp_prod.headers:
    print(f"X-Total-Count: {resp_prod.headers['X-Total-Count']}")

# Contar por categoría
from collections import Counter
cat_counts = Counter(p['categoria_id'] for p in productos)
print(f"\nProductos por categoria_id:")
for cat_id, count in sorted(cat_counts.items()):
    print(f"  categoria_id {cat_id:>2}: {count:>3} productos")
