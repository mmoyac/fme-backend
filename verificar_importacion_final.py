import requests

# Autenticación
API_URL = "https://api.masasestacion.cl"
login_data = {"username": "admin@fme.cl", "password": "admin"}
resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Obtener categorías con su cantidad de productos
resp_cat = requests.get(f"{API_URL}/api/maestras/categorias", headers=headers, params={'tenant_id': 1})
categorias = resp_cat.json()

# Obtener productos (sin límite de paginación)
resp_prod = requests.get(f"{API_URL}/api/productos/", headers=headers, params={'tenant_id': 1, 'limit': 10000})
productos = resp_prod.json()

print("=" * 80)
print("RESUMEN DE IMPORTACIÓN EN PRODUCCIÓN - TENANT 1")
print("=" * 80)

print(f"\n📂 CATEGORÍAS CREADAS: {len(categorias)}")
for cat in categorias:
    productos_cat = [p for p in productos if p['categoria_id'] == cat['id']]
    print(f"   • {cat['codigo']:<20} (ID: {cat['id']:>2}): {len(productos_cat):>3} productos")

print(f"\n📦 TOTAL PRODUCTOS: {len(productos)}")
print("=" * 80)
