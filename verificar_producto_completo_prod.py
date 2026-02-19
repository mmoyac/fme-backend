#!/usr/bin/env python3
"""
Verificar producto completo en producción (con precios formato detallado)
"""
import requests

API_URL = "https://api.masasestacion.cl"
TENANT_ID = 1

# 1. Autenticar
print("🔐 Autenticando...")
resp = requests.post(
    f"{API_URL}/api/auth/token",
    data={
        "username": "admin@fme.cl",
        "password": "admin"
    }
)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Buscar producto 999999
print("\n🔍 Buscando producto SKU 999999...")
resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
productos = resp.json()
producto = next((p for p in productos if p.get('sku') == '999999'), None)

if not producto:
    print("❌ Producto no encontrado")
    exit(1)

print(f"\n✅ Producto encontrado:")
print(f"   ID: {producto['id']}")
print(f"   Nombre: {producto['nombre']}")
print(f"   SKU: {producto['sku']}")
print(f"   Unidad: {producto.get('unidad_medida_id')}")

# 3. Obtener precios
print(f"\n💰 Precios:")
resp = requests.get(f"{API_URL}/api/precios/", headers=headers)
precios = resp.json()

# Filtrar precios de este producto
precios_producto = [p for p in precios if p['producto_id'] == producto['id']]

if not precios_producto:
    print("❌ No hay precios registrados")
else:
    print(f"✅ {len(precios_producto)} precios encontrados:")
    for precio in sorted(precios_producto, key=lambda x: x['local_id']):
        # Obtener nombre del local
        resp_local = requests.get(f"{API_URL}/api/locales/{precio['local_id']}", headers=headers)
        local = resp_local.json()
        print(f"   • {local['codigo']:10s} (ID {precio['local_id']}): ${precio['monto_precio']:>6.0f} - Unidad: {precio['unidad_medida_id']}")

# 4. Obtener inventario
print(f"\n📊 Inventario:")
resp = requests.get(f"{API_URL}/api/inventario/", headers=headers)
inventarios = resp.json()

# Filtrar inventario de este producto
inventarios_producto = [i for i in inventarios if i['producto_id'] == producto['id']]

if not inventarios_producto:
    print("❌ No hay inventario registrado")
else:
    print(f"✅ {len(inventarios_producto)} registros de inventario:")
    for inv in sorted(inventarios_producto, key=lambda x: x['local_id']):
        # Obtener nombre del local
        resp_local = requests.get(f"{API_URL}/api/locales/{inv['local_id']}", headers=headers)
        local = resp_local.json()
        print(f"   • {local['codigo']:10s} (ID {inv['local_id']}): {inv['cantidad_stock']:>3.0f} unidades")

print("\n✅ Verificación completa")
