"""
Script para importar productos, precios e inventario desde Google Sheet.

Uso:
    python importar_completo_desde_sheet_prod.py [--env ENV] [--tenant TENANT_ID] [--sheet SHEET_ID]

Entornos disponibles:
    prod  → https://api.masasestacion.cl          (por defecto)
    dev   → http://localhost:8000

Ejemplos:
    # Importar en producción, tenant 1 con sheet guardado en BD
    python importar_completo_desde_sheet_prod.py --tenant 1

    # Importar en desarrollo, menú interactivo
    python importar_completo_desde_sheet_prod.py --env dev

    # Importar en desarrollo, tenant 1 con sheet personalizado
    python importar_completo_desde_sheet_prod.py --env dev --tenant 1 --sheet 1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM
"""
import sys
import io

# Configurar stdout/stderr para UTF-8 (evitar errores con emojis en Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import argparse
import requests
import csv
import time
from io import StringIO

# ─── Entornos disponibles ─────────────────────────────────────────────────────
ENVIRONMENTS = {
    "prod": {
        "api_url": "https://api.masasestacion.cl",
        "label": "PRODUCCIÓN",
        "user": "admin@fme.cl",
        "password": "admin",
        "docker_container": "masas_estacion_backend",  # docker exec <container>
        "docker_compose": False,
    },
    "dev": {
        "api_url": "http://localhost:8000",
        "label": "DESARROLLO",
        "user": "admin@fme.cl",
        "password": "admin",
        "docker_container": "fme-backend",  # docker compose exec backend
        "docker_compose": True,
    },
}

# ─── Parsear argumentos ───────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Importar datos desde Google Sheet")
parser.add_argument("--env", choices=["prod", "dev"], default=None,
                    help="Entorno destino: 'prod' (producción) o 'dev' (desarrollo local). Si se omite, se pregunta interactivamente.")
parser.add_argument("--tenant", type=int, help="ID del tenant a importar (ej: 1)")
parser.add_argument("--sheet", type=str, help="ID del Google Sheet (anula el valor almacenado en la BD)")
parser.add_argument("--limpiar", action="store_true",
                    help="Eliminar todos los datos operativos del tenant antes de importar (reset completo)")
parser.add_argument("--conservar-clientes", action="store_true",
                    help="Con --limpiar: conserva clientes y sus puntos de fidelización")
args = parser.parse_args()

# ─── Selección de entorno ─────────────────────────────────────────────────────
if args.env:
    ENV_KEY = args.env
else:
    print("=" * 100)
    print("🌍 SELECCIÓN DE ENTORNO")
    print("=" * 100)
    for key, cfg in ENVIRONMENTS.items():
        print(f"   [{key}] {cfg['label']} → {cfg['api_url']}")
    print()
    try:
        ENV_KEY = input("👉 Entorno [prod/dev] (Enter = prod): ").strip().lower() or "prod"
    except EOFError:
        ENV_KEY = "prod"
    if ENV_KEY not in ENVIRONMENTS:
        print(f"❌ Entorno '{ENV_KEY}' no válido. Usa 'prod' o 'dev'.")
        sys.exit(1)

ENV_CFG = ENVIRONMENTS[ENV_KEY]
API_URL = ENV_CFG["api_url"]

# ─── Autenticar para obtener tenants disponibles ─────────────────────────────
print("=" * 100)
print(f"🚀 IMPORTACIÓN COMPLETA — {ENV_CFG['label']}")
print("=" * 100)
print(f"🌐 API: {API_URL}")

_auth_resp = requests.post(
    f"{API_URL}/api/auth/token",
    data={"username": ENV_CFG["user"], "password": ENV_CFG["password"]},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
if _auth_resp.status_code != 200:
    print(f"❌ ERROR al autenticar: {_auth_resp.text}")
    sys.exit(1)

_TOKEN_BOOTSTRAP = _auth_resp.json()["access_token"]
_headers_bootstrap = {"Authorization": f"Bearer {_TOKEN_BOOTSTRAP}"}

# ─── Obtener lista de tenants ─────────────────────────────────────────────────
_tenants_resp = requests.get(f"{API_URL}/api/admin/tenants/", headers=_headers_bootstrap)
if _tenants_resp.status_code != 200:
    print(f"❌ ERROR al obtener tenants: {_tenants_resp.text}")
    sys.exit(1)

_all_tenants = _tenants_resp.json()
_tenants_map = {t["id"]: t for t in _all_tenants}

# ─── Selección interactiva si no se pasaron argumentos ───────────────────────
if args.tenant:
    TENANT_ID = args.tenant
else:
    print("\n📋 TENANTS DISPONIBLES:")
    for t in _all_tenants:
        sheet_info = f"  [sheet: {t.get('google_sheet_id', 'NO CONFIGURADO')}]" if t.get("google_sheet_id") else "  ⚠️  Sin Google Sheet configurado"
        estado = "✅" if t["activo"] else "❌"
        print(f"   {estado} [{t['id']}] {t['nombre']} ({t['codigo']}){sheet_info}")
    print()
    try:
        TENANT_ID = int(input("👉 Ingresa el ID del tenant a importar: ").strip())
    except (ValueError, EOFError):
        print("❌ ID inválido")
        sys.exit(1)

if TENANT_ID not in _tenants_map:
    print(f"❌ Tenant ID {TENANT_ID} no encontrado")
    sys.exit(1)

_tenant_info = _tenants_map[TENANT_ID]

# ─── Determinar SHEET_ID ─────────────────────────────────────────────────────
if args.sheet:
    SHEET_ID = args.sheet.strip()
    print(f"\n📄 Sheet ID suministrado por argumento: {SHEET_ID}")
elif _tenant_info.get("google_sheet_id"):
    SHEET_ID = _tenant_info["google_sheet_id"]
    print(f"\n📄 Sheet ID obtenido desde la BD del tenant: {SHEET_ID}")
else:
    print(f"\n⚠️  El tenant '{_tenant_info['nombre']}' no tiene Google Sheet configurado en la BD.")
    try:
        SHEET_ID = input("👉 Ingresa el Sheet ID manualmente (o Enter para cancelar): ").strip()
    except EOFError:
        SHEET_ID = ""
    if not SHEET_ID:
        print("❌ No se proporcionó Sheet ID. Abortando.")
        sys.exit(1)
    # Ofrecer guardar el sheet en la BD
    try:
        guardar = input(f"💾 ¿Guardar este Sheet ID en la BD para el tenant '{_tenant_info['nombre']}'? [s/N]: ").strip().lower()
    except EOFError:
        guardar = "n"
    if guardar == "s":
        _put_resp = requests.put(
            f"{API_URL}/api/admin/tenants/{TENANT_ID}",
            json={"google_sheet_id": SHEET_ID},
            headers=_headers_bootstrap
        )
        if _put_resp.status_code == 200:
            print(f"   ✅ Sheet ID guardado en la BD")
        else:
            print(f"   ⚠️  No se pudo guardar: {_put_resp.text}")

print()
print(f"📍 Tenant: [{TENANT_ID}] {_tenant_info['nombre']}")
print(f"📄 Google Sheet: {SHEET_ID}")
print(f"📋 Hojas a importar: Categorias, productos, precios, inventario")
print("=" * 100)


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


# ─── Limpieza previa (opcional) ───────────────────────────────────────────────
if args.limpiar:
    import subprocess

    print("\n🗑️  PASO 0: LIMPIEZA PREVIA DEL TENANT")
    print("=" * 100)
    print(f"⚠️  Se eliminarán TODOS los datos operativos de [{TENANT_ID}] {_tenant_info['nombre']}:")
    print("   Pedidos, compras, inventario, precios, lotes, enrolamientos, caja, hojas de ruta...")
    if args.conservar_clientes:
        print("   Clientes: CONSERVADOS (--conservar-clientes activo)")
    else:
        print("   Clientes y puntos de fidelización")
    print("   Productos: CONSERVADOS")

    try:
        confirmar = input("\n¿Confirmar limpieza antes de importar? (SI/NO): ").strip().upper()
    except EOFError:
        confirmar = "NO"

    if confirmar != "SI":
        print("❌ Limpieza cancelada. Abortando importación.")
        sys.exit(0)

    # Construir comando docker según entorno
    delete_cmd = [
        "python", "eliminar_datos_tenant.py",
        f"--tenant-id={TENANT_ID}",
        "--si",  # sin confirmación interactiva (ya confirmamos arriba)
    ]
    if args.conservar_clientes:
        delete_cmd.append("--conservar-clientes")

    if ENV_CFG["docker_compose"]:
        cmd = ["docker", "compose", "exec", "backend"] + delete_cmd
    else:
        cmd = ["docker", "exec", ENV_CFG["docker_container"]] + delete_cmd

    print(f"\n▶  Ejecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"\n❌ La limpieza falló (código {result.returncode}). Abortando importación.")
        sys.exit(1)

    print("\n✅ Limpieza completada. Iniciando importación...")
    print("=" * 100)


            texto += "..."
        return f"[HTTP {status}] {texto}"


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

# 2. Reutilizar token de autenticación ya obtenido
print("\n🔐 PASO 2: Autenticación...")
token = _TOKEN_BOOTSTRAP
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✅ Autenticación exitosa")


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
