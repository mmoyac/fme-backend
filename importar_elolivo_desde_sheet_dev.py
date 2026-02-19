#!/usr/bin/env python3
"""
Script para importar productos, precios e inventario desde Google Sheet a DESARROLLO.
Tenant ID: 2 (El Olivo)
"""
import requests
import csv
from io import StringIO

# Configuración
SHEET_ID = "1gxiX266yYZBQaQpobFPjW0eWm8kk4uxYtKjutLxpv_c"
API_URL = "http://localhost:8000"
TENANT_ID = 2  # El Olivo

print("=" * 100)
print("🚀 IMPORTACIÓN COMPLETA A DESARROLLO - EL OLIVO")
print("=" * 100)
print(f"📍 Tenant: ID {TENANT_ID} (El Olivo)")
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
        
        # Limpiar nombres de columnas (quitar espacios, #, etc.)
        data = []
        for row in reader:
            clean_row = {}
            for key, value in row.items():
                clean_key = key.strip().lstrip('#').strip()  # Quitar # y espacios
                clean_row[clean_key] = value
            data.append(clean_row)
        
        return data
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
    print("❌ ERROR: No se pudieron leer productos. Abortando.")
    exit(1)

# 2. Autenticar en API
print("\n🔐 PASO 2: Autenticando en desarrollo...")

# Intentar primero con credenciales de El Olivo, luego con admin general
credenciales = [
    ("admin@elolivo.cl", "admin"),
    ("admin@fme.cl", "admin")
]

token = None
for email, password in credenciales:
    try:
        resp = requests.post(
            f"{API_URL}/api/auth/token",
            data={"username": email, "password": password}
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            print(f"✅ Autenticación exitosa con {email}")
            break
    except:
        continue

if not token:
    print("❌ ERROR: No se pudo autenticar con ninguna credencial")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# 3. Obtener datos existentes (locales y productos)
print("\n🔍 PASO 3: Obteniendo datos existentes...")

# 3.1. Obtener locales
resp = requests.get(f"{API_URL}/api/locales/", headers=headers)
locales = resp.json()

# USAR TODOS LOS LOCALES (el usuario autenticado solo ve sus locales)
locales_map = {local['codigo']: local['id'] for local in locales}

print(f"✅ Locales disponibles: {len(locales_map)}")
for codigo, local_id in locales_map.items():
    print(f"   • {codigo} (ID: {local_id})")

if not locales_map:
    print("❌ ERROR: No hay locales para el tenant. Abortando.")
    exit(1)

# 3.2. Obtener productos existentes
resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
productos_existentes = resp.json()

# USAR TODOS LOS PRODUCTOS (el usuario autenticado solo ve sus productos)
productos_existentes_map = {p['sku']: p for p in productos_existentes}

print(f"✅ Productos existentes: {len(productos_existentes_map)}")

# 4. Importar productos (crear o actualizar)
print("\n📦 PASO 4: Importando/Actualizando productos...")
print("=" * 100)

productos_creados = {}  # SKU -> id
resultados = {"nuevos": [], "actualizados": [], "fallidos": []}

for producto in productos_data:
    sku = producto.get('sku', '').strip()
    nombre = producto.get('nombre', '').strip()
    descripcion = producto.get('descripcion', '').strip()
    categoria_id = producto.get('categoria_id', '').strip()
    tipo_producto_id = producto.get('tipo_producto_id', '').strip()
    unidad_medida_id = producto.get('unidad_medida_id', '').strip()
    imagen_url = producto.get('imagen_url', '').strip()
    
    # Validar campos obligatorios
    if not sku or not nombre or not categoria_id or not tipo_producto_id or not unidad_medida_id:
        print(f"  ⚠️  SALTADO: Producto incompleto (faltan campos obligatorios)")
        resultados["fallidos"].append({"sku": sku, "nombre": nombre, "error": "Campos incompletos"})
        continue
    
    print(f"\n  {sku} - {nombre}")
    
    # Preparar datos del producto
    producto_data = {
        "tenant_id": TENANT_ID,
        "nombre": nombre,
        "sku": sku,
        "descripcion": descripcion or "",
        "categoria_id": int(categoria_id),
        "tipo_producto_id": int(tipo_producto_id),
        "unidad_medida_id": int(unidad_medida_id),
        "activo": True,
        "es_vendible": True,
        "es_vendible_web": True
    }
    
    if imagen_url:
        producto_data["imagen_url"] = imagen_url
    
    # Verificar si el producto ya existe
    producto_existente = productos_existentes_map.get(sku)
    
    try:
        if producto_existente:
            # ACTUALIZAR producto existente
            producto_id = producto_existente['id']
            resp = requests.put(
                f"{API_URL}/api/productos/{producto_id}",
                json=producto_data,
                headers=headers
            )
            
            if resp.status_code == 200:
                print(f"    ✅ ACTUALIZADO (ID: {producto_id})")
                productos_creados[sku] = producto_id
                resultados["actualizados"].append({"sku": sku, "id": producto_id})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR al actualizar: {error_msg}")
                resultados["fallidos"].append({"sku": sku, "error": error_msg})
        else:
            # CREAR nuevo producto
            resp = requests.post(
                f"{API_URL}/api/productos/",
                json=producto_data,
                headers=headers
            )
            
            if resp.status_code in [200, 201]:
                producto_id = resp.json()["id"]
                print(f"    ✅ CREADO (ID: {producto_id})")
                productos_creados[sku] = producto_id
                resultados["nuevos"].append({"sku": sku, "id": producto_id})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR al crear: {error_msg}")
                resultados["fallidos"].append({"sku": sku, "error": error_msg})
                
    except Exception as e:
        print(f"    ❌ EXCEPCIÓN: {e}")
        resultados["fallidos"].append({"sku": sku, "error": str(e)})

print(f"\n✅ Productos procesados: {len(productos_creados)} ({len(resultados['nuevos'])} nuevos, {len(resultados['actualizados'])} actualizados)")

# 5. Importar precios
if precios_data and productos_creados:
    print("\n💰 PASO 5: Importando precios...")
    print("=" * 100)
    
    resultados_precios = {"exitosos": [], "fallidos": []}
    
    # Primero obtener productos completos con sus unidades de medida
    resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
    # USAR TODOS LOS PRODUCTOS (el usuario autenticado solo ve sus productos)
    productos_full = {p['id']: p for p in resp.json()}
    
    for precio in precios_data:
        sku = precio.get('producto_sku', '').strip()
        codigo_local = precio.get('local_codigo', '').strip()
        monto = precio.get('monto_precio', '').strip()
        
        if not sku or not codigo_local or not monto:
            print(f"⚠️  SALTADO: Precio incompleto")
            continue
        
        # Buscar IDs
        producto_id = productos_creados.get(sku)
        local_id = locales_map.get(codigo_local)
        
        if not producto_id:
            print(f"  ⚠️  SKU {sku} no fue creado, saltando precio")
            resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": "Producto no creado"})
            continue
        
        if not local_id:
            print(f"  ⚠️  Local {codigo_local} no existe, saltando precio")
            resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": "Local no existe"})
            continue
        
        # Obtener unidad_medida_id del producto
        producto_full = productos_full.get(producto_id)
        if not producto_full or 'unidad_medida_id' not in producto_full:
            print(f"  ⚠️  No se puede obtener unidad de medida del producto {sku}")
            resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": "No se pudo obtener unidad de medida"})
            continue
        
        unidad_medida_id = producto_full['unidad_medida_id']
        
        print(f"\n  {sku} en {codigo_local}: ${monto}")
        
        try:
            resp = requests.put(
                f"{API_URL}/api/precios/producto/{producto_id}/local/{local_id}/unidad/{unidad_medida_id}",
                json={"monto_precio": float(monto)},
                headers=headers
            )
            
            if resp.status_code in [200, 201]:
                print(f"    ✅ PRECIO ACTUALIZADO")
                resultados_precios["exitosos"].append({"sku": sku, "local": codigo_local})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
                
        except Exception as e:
            print(f"    ❌ EXCEPCIÓN: {e}")
            resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": str(e)})
    
    print(f"\n✅ Precios actualizados: {len(resultados_precios['exitosos'])}")
else:
    print("\n⚠️  PASO 5: Saltado (no hay precios o productos)")
    resultados_precios = {"exitosos": [], "fallidos": []}

# 6. Importar inventario
if inventario_data and productos_creados:
    print("\n📊 PASO 6: Importando inventario...")
    print("=" * 100)
    
    resultados_inventario = {"exitosos": [], "fallidos": []}
    
    for inv in inventario_data:
        sku = inv.get('producto_sku', '').strip()
        codigo_local = inv.get('local_codigo', '').strip()
        cantidad = inv.get('cantidad_stock', '').strip()
        
        if not sku or not codigo_local or not cantidad:
            print(f"⚠️  SALTADO: Inventario incompleto")
            continue
        
        # Buscar IDs
        producto_id = productos_creados.get(sku)
        local_id = locales_map.get(codigo_local)
        
        if not producto_id:
            print(f"  ⚠️  SKU {sku} no fue creado, saltando inventario")
            resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": "Producto no creado"})
            continue
        
        if not local_id:
            print(f"  ⚠️  Local {codigo_local} no existe, saltando inventario")
            resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": "Local no existe"})
            continue
        
        print(f"\n  {sku} en {codigo_local}: {cantidad} unidades")
        
        try:
            resp = requests.put(
                f"{API_URL}/api/inventario/producto/{producto_id}/local/{local_id}",
                json={"cantidad_stock": int(cantidad)},
                headers=headers
            )
            
            if resp.status_code in [200, 201]:
                print(f"    ✅ INVENTARIO ACTUALIZADO")
                resultados_inventario["exitosos"].append({"sku": sku, "local": codigo_local})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
                
        except Exception as e:
            print(f"    ❌ EXCEPCIÓN: {e}")
            resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": str(e)})
    
    print(f"\n✅ Inventarios actualizados: {len(resultados_inventario['exitosos'])}")
else:
    print("\n⚠️  PASO 6: Saltado (no hay inventario o productos)")
    resultados_inventario = {"exitosos": [], "fallidos": []}

# Resumen final
print("\n" + "=" * 100)
print("📊 RESUMEN FINAL")
print("=" * 100)
print(f"📦 Productos:  ➕ {len(resultados['nuevos']):3d} creados  🔄 {len(resultados['actualizados']):3d} actualizados  ❌ {len(resultados['fallidos']):3d} fallidos")
print(f"💰 Precios:    ✅ {len(resultados_precios['exitosos']):3d}  ❌ {len(resultados_precios['fallidos']):3d}")
print(f"📊 Inventario: ✅ {len(resultados_inventario['exitosos']):3d}  ❌ {len(resultados_inventario['fallidos']):3d}")
print("=" * 100)

if resultados['nuevos']:
    print("\n🔄 PRODUCTOS NUEVOS:")
    for item in resultados['nuevos'][:10]:  # Mostrar primeros 10
        print(f"   • SKU {item['sku']:15s} (ID: {item['id']})")
    if len(resultados['nuevos']) > 10:
        print(f"   ... y {len(resultados['nuevos']) - 10} más")

if resultados['actualizados']:
    print("\n🔄 PRODUCTOS ACTUALIZADOS:")
    for item in resultados['actualizados'][:10]:  # Mostrar primeros 10
        print(f"   • SKU {item['sku']:15s} (ID: {item['id']})")
    if len(resultados['actualizados']) > 10:
        print(f"   ... y {len(resultados['actualizados']) - 10} más")

print("\n" + "=" * 100)
print("🎯 IMPORTACIÓN COMPLETADA")
print("=" * 100)
