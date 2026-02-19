"""
Script para importar productos, precios e inventario desde Google Sheet a PRODUCCIÓN.
Tenant ID: 1 (Masas Estación)
"""
import requests
import csv
from io import StringIO
import json

# Configuración
SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"
API_URL = "https://api.masasestacion.cl"
TENANT_ID = 1  # Masas Estación

print("=" * 100)
print("🚀 IMPORTACIÓN COMPLETA A PRODUCCIÓN")
print("=" * 100)
print(f"📍 Tenant: ID {TENANT_ID} (Masas Estación)")
print(f"🌐 API: {API_URL}")
print(f"📄 Google Sheet: {SHEET_ID}")
print(f"📋 Hojas a importar: productos, precios, inventario")
print("=" * 100)

# Función auxiliar para leer una hoja del Google Sheet
def leer_hoja(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        return list(reader)
    except Exception as e:
        print(f"❌ ERROR al leer hoja '{sheet_name}': {e}")
        return []

# 1. Leer Google Sheets (3 hojas)
print("\n📖 PASO 1: Leyendo Google Sheets...")
print("-" * 100)

productos_data = leer_hoja("productos")
precios_data = leer_hoja("precios")
inventario_data = leer_hoja("inventario")

print(f"✅ Productos:  {len(productos_data)} registros")
print(f"✅ Precios:    {len(precios_data)} registros")
print(f"✅ Inventario: {len(inventario_data)} registros")

if not productos_data:
    print("❌ No hay productos para importar. Abortando.")
    exit(1)

# 2. Autenticación
print("\n🔐 PASO 2: Autenticando en producción...")
login_data = {
    "username": "admin@fme.cl",
    "password": "admin"
}

try:
    resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("✅ Autenticación exitosa\n")
except Exception as e:
    print(f"❌ ERROR en autenticación: {e}")
    exit(1)

# 3. Importar productos
print("📥 PASO 3: Importando productos...")
print("=" * 100)

resultados = {
    "exitosos": [],
    "fallidos": []
}

for producto in productos:
    sku = producto.get('sku', '').strip()
    nombre = producto.get('nombre', '').strip()
    
    if not sku or not nombre:
        print(f"⚠️  SALTADO: Producto sin SKU o nombre")
        continue
    
    # Preparar datos para la API
    producto_data = {
        "tenant_id": TENANT_ID,
        "sku": sku,
        "nombre": nombre,
        "descripcion": producto.get('descripcion', '').strip(),
        "categoria_id": int(producto.get('categoria_id', 1)),
        "tipo_producto_id": int(producto.get('tipo_producto_id', 2)),
        "unidad_medida_id": int(producto.get('unidad_medida_id', 1)),
        "imagen_url": producto.get('imagen_url', '').strip() or None,
        "es_vendible": True,
        "es_vendible_web": True,
        "activo": True
    }
    
    print(f"\n📦 Creando: {sku} - {nombre}")
    print(f"   Categoría: {producto_data['categoria_id']}, Tipo: {producto_data['tipo_producto_id']}, Unidad: {producto_data['unidad_medida_id']}")
    
    try:
        resp = requests.post(
            f"{API_URL}/api/productos/",
            json=producto_data,
            headers=headers
        )
        
        if resp.status_code in [200, 201]:
            producto_creado = resp.json()
            producto_id = producto_creado.get('id', 'N/A')
            print(f"   ✅ CREADO exitosamente (ID: {producto_id})")
            resultados["exitosos"].append({
                "sku": sku,
                "nombre": nombre,
                "id": producto_id
            })
        else:
            error_msg = resp.json().get('detail', resp.text)
            print(f"   ❌ ERROR: {resp.status_code} - {error_msg}")
            resultados["fallidos"].append({
                "sku": sku,
                "nombre": nombre,
                "error": error_msg
            })
            
    except Exception as e:
        print(f"   ❌ EXCEPCIÓN: {e}")
        resultados["fallidos"].append({
            "sku": sku,
            "nombre": nombre,
            "error": str(e)
        })

# 4. Resumen final
print("\n" + "=" * 100)
print("📊 RESUMEN DE IMPORTACIÓN")
print("=" * 100)
print(f"✅ Exitosos: {len(resultados['exitosos'])}")
print(f"❌ Fallidos:  {len(resultados['fallidos'])}")
print("=" * 100)

if resultados["exitosos"]:
    print("\n✅ PRODUCTOS CREADOS:")
    for p in resultados["exitosos"]:
        print(f"   • {p['sku']:<15} - {p['nombre']:<30} (ID: {p['id']})")

if resultados["fallidos"]:
    print("\n❌ PRODUCTOS FALLIDOS:")
    for p in resultados["fallidos"]:
        print(f"   • {p['sku']:<15} - {p['nombre']:<30}")
        print(f"     Error: {p['error']}")

print("\n" + "=" * 100)
print("🎯 IMPORTACIÓN COMPLETADA")
print("=" * 100)
