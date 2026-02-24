"""Script para verificar precios en producción usando solo APIs."""
import requests

API_URL = "https://api.masasestacion.cl"

# 1. Login para obtener token
print("🔐 Obteniendo token de autenticación...")
login_data = {
    "username": "admin@fme.cl",
    "password": "admin"
}
response = requests.post(f"{API_URL}/api/auth/token", data=login_data)
if response.status_code != 200:
    print(f"❌ Error en login: {response.status_code} - {response.text}")
    exit(1)

token = response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✅ Token obtenido")

# 2. Consultar locales
print("\n📍 Consultando locales...")
response = requests.get(f"{API_URL}/api/locales/", headers=headers)
locales = response.json()
print(f"Total locales: {len(locales)}")

locales_dict = {}
for local in locales:
    local_id = local.get("id")
    locales_dict[local_id] = local
    print(f"  - ID {local_id}: {local.get('nombre')} (código: {local.get('codigo')})")

# 3. Consultar precios
print("\n💰 Consultando precios...")
response = requests.get(f"{API_URL}/api/precios/?limit=1000", headers=headers)
precios = response.json()
print(f"Total precios registrados: {len(precios)}")

# Agrupar por local
precios_por_local = {}
for precio in precios:
    local_id = precio.get("local_id")
    if local_id not in precios_por_local:
        precios_por_local[local_id] = []
    precios_por_local[local_id].append(precio)

print("\n📊 Distribución de precios por local:")
for local_id in sorted(locales_dict.keys()):
    local_nombre = locales_dict[local_id].get("nombre")
    local_codigo = locales_dict[local_id].get("codigo")
    count = len(precios_por_local.get(local_id, []))
    print(f"  Local ID {local_id} ({local_codigo} - {local_nombre}): {count} precios")

# 4. Consultar productos
print("\n📦 Consultando productos...")
response = requests.get(f"{API_URL}/api/productos/?limit=1000", headers=headers)
productos = response.json()
print(f"Total productos registrados: {len(productos)}")

# 5. Identificar productos sin precio
productos_con_precio = set()
for precio in precios:
    productos_con_precio.add(precio.get("producto_id"))

productos_sin_precio = [p for p in productos if p.get("id") not in productos_con_precio]

print(f"\n✅ Productos CON precio (en algún local): {len(productos_con_precio)}")
print(f"⚠️ Productos SIN precio (en ningún local): {len(productos_sin_precio)}")

if productos_sin_precio:
    print("\n❌ Lista de productos SIN precio:")
    for prod in productos_sin_precio[:20]:
        print(f"  - ID {prod.get('id'):3d}: {prod.get('nombre'):40s} (SKU: {prod.get('sku')})")
    if len(productos_sin_precio) > 20:
        print(f"  ... y {len(productos_sin_precio) - 20} más")

# 6. Analizar Local Lampa específicamente
print("\n" + "="*60)
print("🔍 ANÁLISIS DETALLADO: LOCAL LAMPA")
print("="*60)

local_lampa = next((l for l in locales if l.get("codigo") == "LAMPA"), None)
if local_lampa:
    lampa_id = local_lampa.get("id")
    print(f"Local Lampa encontrado: ID {lampa_id}, Nombre: {local_lampa.get('nombre')}")
    
    precios_lampa = precios_por_local.get(lampa_id, [])
    print(f"Total precios en Lampa: {len(precios_lampa)}")
    
    if precios_lampa:
        print("\n📊 Muestra de productos con precio en Lampa:")
        for i, precio in enumerate(precios_lampa[:10], 1):
            producto_id = precio.get("producto_id")
            prod = next((p for p in productos if p.get("id") == producto_id), None)
            nombre = prod.get("nombre") if prod else "Desconocido"
            print(f"  {i}. Producto ID {producto_id}: {nombre} - ${precio.get('monto_precio')}")
    else:
        print("⚠️ No hay precios configurados en el local Lampa")
        print("\nRecomendación: Ejecutar script de importación de precios para Lampa")
else:
    print("❌ Local con código LAMPA no encontrado")
