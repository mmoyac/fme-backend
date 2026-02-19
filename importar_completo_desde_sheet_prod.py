"""
Script para importar productos, precios e inventario desde Google Sheet a PRODUCCIÓN.
Tenant ID: 1 (Masas Estación)
"""
import requests
import csv
from io import StringIO

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
    print("✅ Autenticación exitosa")
except Exception as e:
    print(f"❌ ERROR en autenticación: {e}")
    exit(1)

# 3. Obtener productos existentes y mapeo de locales
print("\n🔍 PASO 3: Obteniendo datos existentes...")
try:
    # Obtener locales
    resp = requests.get(f"{API_URL}/api/locales/", headers=headers)
    locales = resp.json()
    locales_map = {local['codigo']: local['id'] for local in locales}
    print(f"✅ Locales disponibles: {len(locales_map)}")
    for codigo in locales_map:
        print(f"   • {codigo} (ID: {locales_map[codigo]})")
    
    # Obtener productos existentes
    resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
    productos_existentes = resp.json()
    productos_existentes_map = {p['sku']: p for p in productos_existentes}
    print(f"✅ Productos existentes: {len(productos_existentes_map)}")
    
except Exception as e:
    print(f"❌ ERROR obteniendo datos: {e}")
    exit(1)

# 4. Importar/Actualizar productos
print("\n📦 PASO 4: Importando/Actualizando productos...")
print("=" * 100)

productos_creados = {}  # SKU -> producto_id
resultados_productos = {"creados": [], "actualizados": [], "fallidos": []}

for producto in productos_data:
    sku = producto.get('sku', '').strip()
    nombre = producto.get('nombre', '').strip()
    
    if not sku or not nombre:
        print(f"⚠️  SALTADO: Producto sin SKU o nombre")
        continue
    
    # Verificar si el producto ya existe
    producto_existente = productos_existentes_map.get(sku)
    producto_id = producto_existente['id'] if producto_existente else None
    
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
    
    if producto_existente:
        # ACTUALIZAR producto existente
        print(f"\n  {sku} - {nombre} (ya existe, actualizando...)")
        try:
            resp = requests.put(
                f"{API_URL}/api/productos/{producto_id}",
                json=producto_data,
                headers=headers
            )
            
            if resp.status_code in [200, 201]:
                print(f"    ✅ ACTUALIZADO (ID: {producto_id})")
                productos_creados[sku] = producto_id
                resultados_productos["actualizados"].append({"sku": sku, "id": producto_id})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
                
        except Exception as e:
            print(f"    ❌ EXCEPCIÓN: {e}")
            resultados_productos["fallidos"].append({"sku": sku, "error": str(e)})
    else:
        # CREAR nuevo producto
        print(f"\n  {sku} - {nombre} (nuevo)")
        try:
            resp = requests.post(
                f"{API_URL}/api/productos/",
                json=producto_data,
                headers=headers
            )
            
            if resp.status_code in [200, 201]:
                producto_creado = resp.json()
                producto_id = producto_creado.get('id')
                print(f"    ✅ CREADO (ID: {producto_id})")
                productos_creados[sku] = producto_id
                resultados_productos["creados"].append({"sku": sku, "id": producto_id})
            else:
                error_msg = resp.json().get('detail', resp.text)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
                
        except Exception as e:
            print(f"    ❌ EXCEPCIÓN: {e}")
            resultados_productos["fallidos"].append({"sku": sku, "error": str(e)})

print(f"\n✅ Productos procesados: {len(productos_creados)} ({len(resultados_productos['creados'])} nuevos, {len(resultados_productos['actualizados'])} actualizados)")

# 5. Importar precios
if precios_data and productos_creados:
    print("\n💰 PASO 5: Importando precios...")
    print("=" * 100)
    
    resultados_precios = {"exitosos": [], "fallidos": []}
    
    # Primero obtener productos completos con sus unidades de medida
    resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
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
    
    for inventario in inventario_data:
        sku = inventario.get('producto_sku', '').strip()
        codigo_local = inventario.get('local_codigo', '').strip()
        cantidad = inventario.get('cantidad_stock', '').strip()
        
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

# 7. Resumen final
print("\n" + "=" * 100)
print("📊 RESUMEN FINAL")
print("=" * 100)
print(f"📦 Productos:  ➕ {len(resultados_productos['creados']):>3} creados  🔄 {len(resultados_productos['actualizados']):>3} actualizados  ❌ {len(resultados_productos['fallidos']):>3} fallidos")
print(f"💰 Precios:    ✅ {len(resultados_precios['exitosos']):>3}  ❌ {len(resultados_precios['fallidos']):>3}")
print(f"📊 Inventario: ✅ {len(resultados_inventario['exitosos']):>3}  ❌ {len(resultados_inventario['fallidos']):>3}")
print("=" * 100)

if resultados_productos["creados"]:
    print("\n➕ PRODUCTOS NUEVOS:")
    for p in resultados_productos["creados"]:
        print(f"   • SKU {p['sku']:<15} (ID: {p['id']})")

if resultados_productos["actualizados"]:
    print("\n🔄 PRODUCTOS ACTUALIZADOS:")
    for p in resultados_productos["actualizados"]:
        print(f"   • SKU {p['sku']:<15} (ID: {p['id']})")

if resultados_productos["fallidos"]:
    print("\n❌ PRODUCTOS FALLIDOS:")
    for p in resultados_productos["fallidos"]:
        print(f"   • SKU {p['sku']:<15} - {p['error']}")

print("\n" + "=" * 100)
print("🎯 IMPORTACIÓN COMPLETADA")
print("=" * 100)
