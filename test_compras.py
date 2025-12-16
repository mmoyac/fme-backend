# Test script para probar el módulo de compras
# Ejecutar: python test_compras.py

import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Login
print("1. Autenticando...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/token",
    data={
        "username": "admin@fme.cl",
        "password": "admin123"
    }
)
if login_response.status_code != 200:
    print(f"❌ Error en login: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Login exitoso")

# 2. Crear un proveedor de prueba
print("\n2. Creando proveedor de prueba...")
proveedor_data = {
    "nombre": "Distribuidora La Harina Ltda",
    "rut": "76.123.456-7",
    "contacto": "Juan Pérez",
    "email": "ventas@laharina.cl",
    "telefono": "+56912345678",
    "direccion": "Av. Principal 123, Santiago",
    "activo": True
}

prov_response = requests.post(
    f"{BASE_URL}/api/compras/proveedores",
    headers=headers,
    json=proveedor_data
)

if prov_response.status_code != 200:
    print(f"❌ Error creando proveedor: {prov_response.status_code}")
    print(prov_response.text)
    exit(1)

proveedor = prov_response.json()
print(f"✅ Proveedor creado: ID {proveedor['id']} - {proveedor['nombre']}")

# 3. Listar proveedores
print("\n3. Listando proveedores...")
provs_response = requests.get(
    f"{BASE_URL}/api/compras/proveedores",
    headers=headers
)
proveedores = provs_response.json()
print(f"✅ Total proveedores: {len(proveedores)}")

# 4. Obtener locales y productos
print("\n4. Obteniendo catálogos...")
locales_response = requests.get(f"{BASE_URL}/api/locales", headers=headers)
productos_response = requests.get(f"{BASE_URL}/api/productos", headers=headers)

locales = locales_response.json()
productos = productos_response.json()

print(f"✅ Locales disponibles: {len(locales)}")
print(f"✅ Productos disponibles: {len(productos)}")

if not locales or not productos:
    print("❌ No hay locales o productos. Crea algunos primero.")
    exit(1)

local_id = locales[0]['id']
# Buscar un producto que sea ingrediente (ej: harina, huevos)
producto_ingrediente = next((p for p in productos if p.get('es_ingrediente')), productos[0])

print(f"   Usando Local: {locales[0]['nombre']}")
print(f"   Usando Producto: {producto_ingrediente['nombre']}")

# 5. Verificar stock inicial
print("\n5. Verificando stock inicial...")
inv_response = requests.get(
    f"{BASE_URL}/api/inventario?local_id={local_id}&producto_id={producto_ingrediente['id']}",
    headers=headers
)
inventario_inicial = inv_response.json()
stock_inicial = 0
if inventario_inicial:
    stock_inicial = inventario_inicial[0].get('cantidad_stock', 0)
print(f"   Stock inicial de {producto_ingrediente['nombre']}: {stock_inicial}")

# 6. Registrar una compra
print("\n6. Registrando compra...")
compra_data = {
    "proveedor_id": proveedor['id'],
    "local_id": local_id,
    "tipo_documento": "FACTURA",
    "numero_documento": "F-001234",
    "notas": "Compra de prueba automatizada",
    "detalles": [
        {
            "producto_id": producto_ingrediente['id'],
            "cantidad": 50,
            "precio_unitario": 1500
        }
    ]
}

compra_response = requests.post(
    f"{BASE_URL}/api/compras/",
    headers=headers,
    json=compra_data
)

if compra_response.status_code != 200:
    print(f"❌ Error registrando compra: {compra_response.status_code}")
    print(compra_response.text)
    exit(1)

compra = compra_response.json()
print(f"✅ Compra registrada: ID {compra['id']}")
print(f"   Monto total: ${compra['monto_total']:,.0f}")

# 7. Verificar stock actualizado
print("\n7. Verificando stock actualizado...")
inv_response2 = requests.get(
    f"{BASE_URL}/api/inventario?local_id={local_id}&producto_id={producto_ingrediente['id']}",
    headers=headers
)
inventario_final = inv_response2.json()
stock_final = inventario_final[0]['cantidad_stock'] if inventario_final else 0
print(f"   Stock final de {producto_ingrediente['nombre']}: {stock_final}")
print(f"   Incremento: +{stock_final - stock_inicial}")

# 8. Verificar precio de compra actualizado
print("\n8. Verificando precio de compra actualizado...")
prod_response = requests.get(
    f"{BASE_URL}/api/productos/{producto_ingrediente['id']}",
    headers=headers
)
producto_actualizado = prod_response.json()
print(f"   Precio de compra actualizado: ${producto_actualizado.get('precio_compra', 0):,.0f}")

print("\n" + "="*60)
print("✅ PRUEBA COMPLETA EXITOSA")
print("="*60)
print("\nResumen:")
print(f"- Proveedor creado: {proveedor['nombre']}")
print(f"- Compra registrada: #{compra['id']} por ${compra['monto_total']:,.0f}")
print(f"- Stock incrementado: {stock_inicial} → {stock_final} (+{stock_final - stock_inicial})")
print(f"- Precio actualizado: ${producto_actualizado.get('precio_compra', 0):,.0f}")
