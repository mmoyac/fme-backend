"""
Script para importar productos, precios e inventario desde Google Sheet a PRODUCCIÓN.
Tenant ID: 1 (Masas Estación)
"""
import sys
import io

# Configurar stdout/stderr para UTF-8 (evitar errores con emojis en Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import csv
import time
from io import StringIO

# Configuración
SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"
API_URL = "https://api.masasestacion.cl"
TENANT_ID = 1  # Masas Estación


def obtener_detalle_error(resp):
    """Extrae información detallada del error de una respuesta HTTP."""
    status = resp.status_code
    
    # Intentar parsear como JSON
    try:
        error_data = resp.json()
        if isinstance(error_data, dict):
            detail = error_data.get('detail', str(error_data))
        else:
            detail = str(error_data)
        return f"[HTTP {status}] {detail}"
    except:
        # No es JSON, mostrar texto raw (truncado si es muy largo)
        texto = resp.text[:300] if resp.text else "(respuesta vacía)"
        if len(resp.text) > 300:
            texto += "..."
        return f"[HTTP {status}] {texto}"


print("=" * 100)
print("🚀 IMPORTACIÓN COMPLETA A PRODUCCIÓN")
print("=" * 100)
print(f"📍 Tenant: ID {TENANT_ID} (Masas Estación)")
print(f"🌐 API: {API_URL}")
print(f"📄 Google Sheet: {SHEET_ID}")
print(f"📋 Hojas a importar: Categorias, productos, precios, inventario")
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

# 1. Leer Google Sheets (4 hojas)
print("\n📖 PASO 1: Leyendo Google Sheets...")
print("-" * 100)

categorias_data = leer_hoja("Categorias")
productos_data = leer_hoja("productos")
precios_data = leer_hoja("precios")
inventario_data = leer_hoja("inventario")

print(f"✅ Categorías: {len(categorias_data)} registros")
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

# 3. Sincronizar Categorías (crear las que no existen)
print("\n📂 PASO 3: Sincronizando categorías...")
print("-" * 100)

categoria_id_mapeo = {}  # id_sheet -> id_produccion

if categorias_data:
    try:
        # Obtener categorías existentes en producción
        resp = requests.get(f"{API_URL}/api/maestras/categorias", headers=headers, params={'tenant_id': TENANT_ID})
        categorias_existentes = resp.json() if resp.status_code == 200 else []
        categorias_por_codigo = {c['codigo']: c for c in categorias_existentes}
        
        print(f"✅ Categorías existentes en producción: {len(categorias_existentes)}")
        
        # Procesar categorías del sheet
        for cat_sheet in categorias_data:
            id_sheet = cat_sheet.get('id', '').strip()
            codigo = cat_sheet.get('codigo', '').strip().upper()
            nombre = cat_sheet.get('nombre', '').strip()
            
            if not codigo or not nombre:
                continue
                
            # Verificar si ya existe
            if codigo in categorias_por_codigo:
                cat_prod = categorias_por_codigo[codigo]
                categoria_id_mapeo[id_sheet] = cat_prod['id']
                print(f"  ℹ️  {codigo:<15} → ID {cat_prod['id']:>3} (ya existe)")
            else:
                # Crear nueva categoría
                nueva_categoria = {
                    "tenant_id": TENANT_ID,
                    "codigo": codigo,
                    "nombre": nombre,
                    "descripcion": cat_sheet.get('descripcion', '').strip() or nombre,
                    "puntos_fidelidad": int(cat_sheet.get('puntos_ganados', 0) or 0),
                    "activo": cat_sheet.get('activo', 'TRUE').upper() == 'TRUE'
                }
                
                resp = requests.post(
                    f"{API_URL}/api/maestras/categorias",
                    json=nueva_categoria,
                    headers=headers
                )
                
                if resp.status_code in [200, 201]:
                    cat_creada = resp.json()
                    categoria_id_mapeo[id_sheet] = cat_creada['id']
                    print(f"  ✅ {codigo:<15} → ID {cat_creada['id']:>3} (NUEVA)")
                else:
                    error_msg = obtener_detalle_error(resp)
                    print(f"  ❌ {codigo:<15} Error: {error_msg}")
        
        print(f"✅ Mapeo de categorías completado: {len(categoria_id_mapeo)} categorías")
        
    except Exception as e:
        print(f"❌ ERROR sincronizando categorías: {e}")
        print("⚠️  Continuando con categorías existentes...")
        categoria_id_mapeo = {}
else:
    print("⚠️  No hay categorías en el sheet, usando las existentes")

# 4. Obtener productos existentes y mapeo de locales
print("\n🔍 PASO 4: Obteniendo datos existentes...")
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

# 5. Importar/Actualizar productos
print("\n📦 PASO 5: Importando/Actualizando productos...")
print("=" * 100)

productos_creados = {}  # SKU -> producto_id
resultados_productos = {"creados": [], "actualizados": [], "fallidos": []}

# Configuración de throttling (prevenir saturación del backend)
THROTTLE_CADA_N_PRODUCTOS = 20  # Pausa cada N productos
THROTTLE_SLEEP_SEGUNDOS = 0.5     # Segundos de pausa
contador_productos = 0

for producto in productos_data:
    sku = producto.get('sku', '').strip()
    nombre = producto.get('nombre', '').strip()
    
    if not sku or not nombre:
        print(f"⚠️  SALTADO: Producto sin SKU o nombre")
        continue
    
    # Verificar si el producto ya existe
    producto_existente = productos_existentes_map.get(sku)
    producto_id = producto_existente['id'] if producto_existente else None
    
    # Obtener categoria_id del sheet y mapear al ID de producción
    categoria_id_sheet = producto.get('categoria_id', '').strip()
    categoria_id_final = categoria_id_mapeo.get(categoria_id_sheet, 1)  # Default: General (1)
    
    # Preparar datos para la API
    producto_data = {
        "tenant_id": TENANT_ID,
        "sku": sku,
        "nombre": nombre,
        "descripcion": producto.get('descripcion', '').strip(),
        "categoria_id": categoria_id_final,
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
                error_msg = obtener_detalle_error(resp)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
                
        except Exception as e:
            error_msg = f"Excepción durante actualización: {str(e)}"
            print(f"    ❌ {error_msg}")
            resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
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
                error_msg = obtener_detalle_error(resp)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
                
        except Exception as e:
            error_msg = f"Excepción durante creación: {str(e)}"
            print(f"    ❌ {error_msg}")
            resultados_productos["fallidos"].append({"sku": sku, "error": error_msg})
    
    # Aplicar throttling (pausa cada N productos)
    contador_productos += 1
    if contador_productos % THROTTLE_CADA_N_PRODUCTOS == 0:
        print(f"\n  ⏸️  Pausa preventiva ({contador_productos} productos procesados)...")
        time.sleep(THROTTLE_SLEEP_SEGUNDOS)

print(f"\n✅ Productos procesados: {len(productos_creados)} ({len(resultados_productos['creados'])} nuevos, {len(resultados_productos['actualizados'])} actualizados)")

# 6. Importar precios
if precios_data and productos_creados:
    print("\n💰 PASO 6: Importando precios...")
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
                error_msg = obtener_detalle_error(resp)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
                
        except Exception as e:
            error_msg = f"Excepción durante actualización de precio: {str(e)}"
            print(f"    ❌ {error_msg}")
            resultados_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
    
    print(f"\n✅ Precios actualizados: {len(resultados_precios['exitosos'])}")
else:
    print("\n⚠️  PASO 6: Saltado (no hay precios o productos)")
    resultados_precios = {"exitosos": [], "fallidos": []}

# 7. Importar inventario
if inventario_data and productos_creados:
    print("\n📊 PASO 7: Importando inventario...")
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
                error_msg = obtener_detalle_error(resp)
                print(f"    ❌ ERROR: {error_msg}")
                resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
                
        except Exception as e:
            error_msg = f"Excepción durante actualización de inventario: {str(e)}"
            print(f"    ❌ {error_msg}")
            resultados_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": error_msg})
    
    print(f"\n✅ Inventarios actualizados: {len(resultados_inventario['exitosos'])}")
else:
    print("\n⚠️  PASO 7: Saltado (no hay inventario o productos)")
    resultados_inventario = {"exitosos": [], "fallidos": []}

# 8. Resumen final
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
