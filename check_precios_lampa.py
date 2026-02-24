"""Script para verificar precios en local Lampa."""
import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBtYXNhc2VzdGFjaW9uLmNsIiwiZXhwIjoxNzQwMzQxMjgxfQ.b9Q1KCGl92d6ddOuXSNu-rNwOJxg0b03UYoCk5SX_vI"
}

print("📡 Consultando precios en producción...")
response = requests.get("https://api.masasestacion.cl/api/precios/?limit=1000", headers=headers)
print(f"Response status: {response.status_code}")
print(f"Response type: {type(response.text)}")
print(f"Response content: {response.text[:500]}")
data = response.json()
print(f"Data type: {type(data)}")

if isinstance(data, list):
    print(f"\n✅ Total precios registrados: {len(data)}")
else:
    print(f"\n⚠️ Respuesta inesperada: {data}")
    exit(1)

# Agrupar por local_id
precios_por_local = {}
for precio in data:
    local_id = precio.get("local_id")
    if local_id not in precios_por_local:
        precios_por_local[local_id] = []
    precios_por_local[local_id].append(precio)

print("\n📊 Distribución de precios por local:")
for local_id, precios in sorted(precios_por_local.items()):
    print(f"  Local ID {local_id}: {len(precios)} precios")

# Verificar locales
print("\n📍 Consultando locales...")
response_locales = requests.get("https://api.masasestacion.cl/api/locales/", headers=headers)
locales = response_locales.json()

print("\n🏢 Locales registrados:")
for local in locales:
    local_id = local.get("id")
    nombre = local.get("nombre")
    codigo = local.get("codigo")
    precios_count = len(precios_por_local.get(local_id, []))
    print(f"  ID {local_id}: {nombre} (código: {codigo}) - {precios_count} precios")

# Detalles del Local ID 1
precios_lampa = precios_por_local.get(1, [])
print(f"\n🔍 Detalles Local ID 1:")
if precios_lampa:
    print(f"  Total precios: {len(precios_lampa)}")
    print(f"  Muestra de productos con precio:")
    for precio in precios_lampa[:10]:
        print(f"    - Producto ID {precio.get('producto_id')}: ${precio.get('monto_precio')}")
else:
    print("  ⚠️ Sin precios registrados en Local ID 1")

# Verificar productos sin precio en ningún local
print("\n🔄 Consultando productos...")
response_productos = requests.get("https://api.masasestacion.cl/api/productos/?limit=1000", headers=headers)
productos = response_productos.json()

productos_con_precio = set()
for precio in data:
    productos_con_precio.add(precio.get("producto_id"))

productos_sin_precio = [p for p in productos if p.get("id") not in productos_con_precio]

print(f"\n📦 Total productos registrados: {len(productos)}")
print(f"✅ Productos con precio (cualquier local): {len(productos_con_precio)}")
print(f"⚠️ Productos SIN precio en ningún local: {len(productos_sin_precio)}")

if productos_sin_precio:
    print("\n❌ Productos sin precio:")
    for prod in productos_sin_precio[:10]:
        print(f"  - ID {prod.get('id')}: {prod.get('nombre')} (SKU: {prod.get('sku')})")
    if len(productos_sin_precio) > 10:
        print(f"  ... y {len(productos_sin_precio) - 10} más")
