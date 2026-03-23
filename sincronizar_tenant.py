#!/usr/bin/env python
"""
Script unificado: limpia datos de un tenant e importa desde Google Sheet.

Uso (interactivo — recomendado):
    python sincronizar_tenant.py

Uso con argumentos (automatización / CI):
    python sincronizar_tenant.py --env dev --tenant 1 --user admin@fme.cl --password admin
    python sincronizar_tenant.py --env prod --tenant 3 --user admin@elolivo.cl --password pass --sheet 1acE1CN_...
    python sincronizar_tenant.py --env prod --tenant 3 --user admin@elolivo.cl --password pass --limpiar --si

Flags:
    --env          prod | dev  (si se omite, se pregunta)
    --tenant       ID del tenant (si se omite, se muestra menú)
    --user         Email del usuario que autenticará (debe pertenecer al tenant)
    --password     Contraseña del usuario
    --sheet        Sheet ID (anula el guardado en BD)
    --limpiar      Limpiar datos antes de importar (se pregunta si se omite)
    --solo-limpiar Solo limpiar, no importar
    --eliminar-clientes   Con --limpiar: también elimina clientes y puntos (por defecto se conservan)
    --eliminar-productos  Con --limpiar: también elimina productos (por defecto se conservan)
    --si           Confirma todas las preguntas automáticamente

Nota: si --user/--password no se proveen, se usan los defaults del entorno.
      El usuario debe pertenecer al tenant seleccionado.
"""
import sys
import io
import argparse
import subprocess
import requests
import csv
import time
from io import StringIO

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ─── Entornos ─────────────────────────────────────────────────────────────────
ENVIRONMENTS = {
    "prod": {
        "api_url":          "https://api.masasestacion.cl",
        "label":            "PRODUCCIÓN",
        "user":             "admin@fme.cl",
        "password":         "admin",
        "docker_container": "masas_estacion_backend",
        "docker_compose":   False,
        "ssh_host":         "168.231.96.205",
    },
    "dev": {
        "api_url":          "http://localhost:8000",
        "label":            "DESARROLLO",
        "user":             "admin@fme.cl",
        "password":         "admin",
        "docker_container": "fme-backend",
        "docker_compose":   True,
    },
}

SEP = "=" * 90

# ─── Argumentos ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Sincronizar tenant desde Google Sheet")
parser.add_argument("--env",    choices=["prod", "dev"], default=None)
parser.add_argument("--tenant", type=int,  default=None, help="ID del tenant")
parser.add_argument("--sheet",  type=str,  default=None, help="Sheet ID (anula BD)")
parser.add_argument("--user",   type=str,  default=None, help="Email del usuario (debe pertenecer al tenant)")
parser.add_argument("--password", type=str, default=None, help="Contraseña del usuario")
parser.add_argument("--limpiar",       action="store_true", help="Limpiar antes de importar")
parser.add_argument("--solo-limpiar",  action="store_true", help="Solo limpiar, no importar")
parser.add_argument("--eliminar-clientes", action="store_true", help="Con --limpiar: eliminar también clientes y puntos")
parser.add_argument("--eliminar-productos", action="store_true", help="Con --limpiar: eliminar también productos (por defecto se conservan)")
parser.add_argument("--si", action="store_true", help="Auto-confirmar todo")
args = parser.parse_args()


def preguntar(mensaje, opciones=None, default=None):
    """Pide input al usuario. Con --si devuelve default automáticamente."""
    if args.si:
        return default
    try:
        respuesta = input(mensaje).strip()
        return respuesta if respuesta else default
    except EOFError:
        return default


def confirmar(mensaje):
    """Retorna True si el usuario confirma (o --si está activo)."""
    if args.si:
        return True
    r = preguntar(f"{mensaje} (SI/no): ", default="SI")
    return r.upper() in ("SI", "S", "Y", "YES", "")


# ═══════════════════════════════════════════════════════════════════════════════
# PASO 0 — Entorno
# ═══════════════════════════════════════════════════════════════════════════════
print(SEP)
print("🔄  SINCRONIZACIÓN DE TENANT DESDE GOOGLE SHEET")
print(SEP)

if args.env:
    ENV_KEY = args.env
else:
    print("\n🌍 ENTORNO:")
    for key, cfg in ENVIRONMENTS.items():
        print(f"   [{key}]  {cfg['label']}  →  {cfg['api_url']}")
    ENV_KEY = preguntar("\n👉 Entorno [prod/dev] (Enter = prod): ", default="prod").lower()
    if ENV_KEY not in ENVIRONMENTS:
        print(f"❌ Entorno inválido: '{ENV_KEY}'")
        sys.exit(1)

ENV = ENVIRONMENTS[ENV_KEY]
API_URL = ENV["api_url"]
print(f"\n✅ Entorno: {ENV['label']}  ({API_URL})")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Autenticar
# ═══════════════════════════════════════════════════════════════════════════════
def autenticar(email, password):
    resp = requests.post(
        f"{API_URL}/api/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 200:
        return None
    return resp.json()["access_token"]

# Credenciales: --user/--password tienen prioridad, luego los defaults del entorno
_auth_email    = args.user     or ENV["user"]
_auth_password = args.password or ENV["password"]

TOKEN = autenticar(_auth_email, _auth_password)
if not TOKEN:
    print(f"❌ Autenticación fallida para {_auth_email}")
    sys.exit(1)
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print(f"✅ Autenticado correctamente ({_auth_email})")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Seleccionar tenant
# ═══════════════════════════════════════════════════════════════════════════════
_r = requests.get(f"{API_URL}/api/tenants/", headers=HEADERS)
if _r.status_code != 200:
    print(f"❌ No se pudieron obtener tenants: {_r.text}")
    sys.exit(1)

ALL_TENANTS = {t["id"]: t for t in _r.json()}

if args.tenant:
    TENANT_ID = args.tenant
else:
    print(f"\n{SEP}")
    print("🏢 TENANTS DISPONIBLES:")
    for t in ALL_TENANTS.values():
        sheet_info = f"  [sheet: {t.get('google_sheet_id')}]" if t.get("google_sheet_id") else "  ⚠️  sin sheet"
        estado = "✅" if t["activo"] else "❌"
        print(f"   {estado} [{t['id']}] {t['nombre']} ({t['codigo']}){sheet_info}")
    TENANT_ID = int(preguntar("\n👉 ID del tenant: ", default="1"))

if TENANT_ID not in ALL_TENANTS:
    print(f"❌ Tenant ID {TENANT_ID} no encontrado")
    sys.exit(1)

TENANT = ALL_TENANTS[TENANT_ID]
print(f"✅ Tenant: [{TENANT_ID}] {TENANT['nombre']}")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 2b — Verificar que el usuario autenticado pertenece al tenant seleccionado.
# ═══════════════════════════════════════════════════════════════════════════════
_me = requests.get(f"{API_URL}/api/auth/users/me", headers=HEADERS)
AUTH_TENANT_ID = _me.json().get("tenant_id") if _me.status_code == 200 else None

if AUTH_TENANT_ID != TENANT_ID:
    print(f"\n❌ El usuario '{_auth_email}' pertenece al tenant {AUTH_TENANT_ID}, pero se seleccionó el tenant {TENANT_ID}.")
    print(f"   Usa --user y --password con credenciales de un usuario del tenant {TENANT_ID}.")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Limpiar datos (opcional)
# ═══════════════════════════════════════════════════════════════════════════════
HACER_LIMPIEZA = args.limpiar or args.solo_limpiar

if not HACER_LIMPIEZA and not args.si:
    print(f"\n{SEP}")
    print("🗑️  LIMPIEZA PREVIA")
    print(f"   Elimina todos los datos operativos de [{TENANT_ID}] {TENANT['nombre']}")
    print("   (pedidos, compras, inventario, precios, lotes, caja...)")
    print("   Productos, Locales, Usuarios y Proveedores se CONSERVAN")
    HACER_LIMPIEZA = confirmar("\n¿Limpiar datos antes de importar?")

if HACER_LIMPIEZA:
    print(f"\n{SEP}")
    print(f"🗑️  LIMPIANDO TENANT [{TENANT_ID}] {TENANT['nombre']}...")
    print(SEP)

    if not args.si:
        print("⚠️  Esta operación es IRREVERSIBLE.")
        if not confirmar("¿Confirmar limpieza?"):
            print("❌ Limpieza cancelada.")
            if args.solo_limpiar:
                sys.exit(0)
            HACER_LIMPIEZA = False

if HACER_LIMPIEZA:
    delete_cmd = ["python", "eliminar_datos_tenant.py", f"--tenant-id={TENANT_ID}", "--si"]
    if args.eliminar_clientes:
        delete_cmd.append("--eliminar-clientes")
    if args.eliminar_productos:
        delete_cmd.append("--eliminar-productos")

    if ENV["docker_compose"]:
        cmd = ["docker", "compose", "exec", "backend"] + delete_cmd
    elif ENV.get("ssh_host"):
        # Producción remota: ejecutar vía SSH
        remote_cmd = "docker exec " + ENV["docker_container"] + " " + " ".join(delete_cmd)
        cmd = ["ssh", f"root@{ENV['ssh_host']}", remote_cmd]
    else:
        cmd = ["docker", "exec", ENV["docker_container"]] + delete_cmd

    print(f"▶  {' '.join(cmd)}\n")
    result = subprocess.run(cmd, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"\n❌ Limpieza fallida (código {result.returncode}). Abortando.")
        sys.exit(1)
    print("\n✅ Limpieza completada")

if args.solo_limpiar:
    print("\n✅ Solo limpieza solicitada. Fin.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Determinar Google Sheet ID
# ═══════════════════════════════════════════════════════════════════════════════
def extraer_sheet_id(raw: str) -> str:
    """Extrae solo el ID base de una URL completa de Google Sheets o de un ID puro."""
    import re as _re
    raw = raw.strip()
    # Caso: URL completa tipo https://docs.google.com/spreadsheets/d/{ID}/edit...
    m = _re.search(r"spreadsheets/d/([a-zA-Z0-9_-]+)", raw)
    if m:
        return m.group(1)
    # Caso: ID seguido de /edit?... o /edit#...
    m = _re.match(r"([a-zA-Z0-9_-]+)(?:[/?#].*)?$", raw)
    if m:
        return m.group(1)
    return raw

if args.sheet:
    SHEET_ID = extraer_sheet_id(args.sheet)
    print(f"\n📄 Sheet ID: {SHEET_ID}  (vía argumento)")
elif TENANT.get("google_sheet_id"):
    SHEET_ID = extraer_sheet_id(TENANT["google_sheet_id"])
    print(f"\n📄 Sheet ID: {SHEET_ID}  (desde BD)")
else:
    print(f"\n⚠️  El tenant '{TENANT['nombre']}' no tiene Sheet ID en la BD.")
    SHEET_ID = preguntar("👉 Ingresa el Sheet ID (o Enter para cancelar): ", default="")
    if not SHEET_ID:
        print("❌ Sin Sheet ID. Abortando.")
        sys.exit(1)
    if confirmar(f"💾 ¿Guardar Sheet ID en BD para este tenant?"):
        _put = requests.put(
            f"{API_URL}/api/tenants/{TENANT_ID}",
            json={"google_sheet_id": SHEET_ID},
            headers=HEADERS,
        )
        print("   ✅ Guardado" if _put.status_code == 200 else f"   ⚠️  No guardado: {_put.text}")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Leer Google Sheets
# ═══════════════════════════════════════════════════════════════════════════════
THROTTLE_CADA_N = 20
THROTTLE_SLEEP  = 0.5

print(f"\n{SEP}")
print("📖 LEYENDO GOOGLE SHEETS...")
print(SEP)


def leer_hoja(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = []
        for row in csv.DictReader(StringIO(r.text)):
            clean = {k.strip().lstrip('#').strip(): v for k, v in row.items()}
            data.append(clean)
        return data
    except Exception as e:
        print(f"❌ Error al leer hoja '{sheet_name}': {e}")
        return []


def detalle_error(resp):
    try:
        d = resp.json()
        detail = d.get('detail', str(d)) if isinstance(d, dict) else str(d)
    except Exception:
        detail = resp.text[:300] + ("..." if len(resp.text) > 300 else "")
    return f"[HTTP {resp.status_code}] {detail}"


def get_or_create_local(codigo_local):
    """Devuelve local_id para codigo_local, creando el local si no existe."""
    if codigo_local in locales_map:
        return locales_map[codigo_local]
    # Intentar crear el local con el codigo como nombre
    r = requests.post(
        f"{API_URL}/api/locales/",
        json={"nombre": codigo_local, "codigo": codigo_local},
        headers=HEADERS,
    )
    if r.status_code in (200, 201):
        nuevo = r.json()
        locales_map[codigo_local] = nuevo["id"]
        print(f"    ✅ Local '{codigo_local}' creado (ID {nuevo['id']}, código asignado: {nuevo['codigo']})")
        return nuevo["id"]
    elif r.status_code == 400:
        # Ya existe un local con ese nombre o código — buscarlo en la lista
        r2 = requests.get(f"{API_URL}/api/locales/", headers=HEADERS)
        if r2.status_code == 200:
            for loc in r2.json():
                if loc.get("codigo") == codigo_local or loc.get("nombre") == codigo_local:
                    locales_map[codigo_local] = loc["id"]
                    print(f"    ✅ Local '{codigo_local}' encontrado (ID {loc['id']})")
                    return loc["id"]
        print(f"    ❌ No se pudo crear ni encontrar local '{codigo_local}': {detalle_error(r)}")
        return None
    else:
        print(f"    ❌ No se pudo crear local '{codigo_local}': {detalle_error(r)}")
        return None


categorias_data  = leer_hoja("Categorias")
productos_data          = leer_hoja("productos")
precios_data            = leer_hoja("precios")
inventario_data         = leer_hoja("inventario")
tipos_proveedor_data    = leer_hoja("Tipo_Proveedor")
proveedores_data        = leer_hoja("proveedores")
precios_proveedor_data  = leer_hoja("precios_proveedor")
locales_data            = leer_hoja("Locales")

print(f"   Categorías:           {len(categorias_data)} registros")
print(f"   Locales:              {len(locales_data)} registros")
print(f"   Productos:            {len(productos_data)} registros")
print(f"   Precios:              {len(precios_data)} registros")
print(f"   Inventario:           {len(inventario_data)} registros")
print(f"   Tipos de proveedor:   {len(tipos_proveedor_data)} registros")
print(f"   Proveedores:          {len(proveedores_data)} registros")
print(f"   Precios proveedor:    {len(precios_proveedor_data)} registros")

if not productos_data:
    print("❌ No hay productos en el Sheet. Abortando.")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 5.5 — Sincronizar locales
# ═══════════════════════════════════════════════════════════════════════════════
res_locales = {"creados": 0, "actualizados": 0, "fallidos": 0}

if locales_data:
    print(f"\n{SEP}")
    print("🏪 SINCRONIZANDO LOCALES...")
    print(SEP)

    # Recargar locales_map desde la BD
    r = requests.get(f"{API_URL}/api/locales/", headers=HEADERS)
    locales_actuales = r.json() if r.status_code == 200 else []
    locales_map = {l["codigo"]: l["id"] for l in locales_actuales}
    locales_por_nombre = {l["nombre"]: l for l in locales_actuales}

    for loc in locales_data:
        codigo   = loc.get("codigo", "").strip().upper()
        nombre   = loc.get("nombre", "").strip()
        if not nombre:
            print(f"   ⚠️  SALTADO (falta nombre): {dict(list(loc.items())[:3])}")
            continue
        if not codigo:
            codigo = None

        direccion  = loc.get("direccion", "").strip() or None
        activo_str = loc.get("activo", "true").strip().lower()
        activo     = activo_str not in ("false", "0", "no")

        print(f"\n  {codigo or '(auto)'} — {nombre}")

        # Buscar por codigo o por nombre
        existente = locales_map.get(codigo) if codigo else None
        if existente is None:
            loc_por_nombre = locales_por_nombre.get(nombre)
            if loc_por_nombre:
                existente = loc_por_nombre["id"]

        payload = {"nombre": nombre, "activo": activo}
        if codigo:
            payload["codigo"] = codigo
        if direccion:
            payload["direccion"] = direccion

        try:
            if existente:
                r2 = requests.put(f"{API_URL}/api/locales/{existente}", json=payload, headers=HEADERS)
                if r2.status_code in (200, 201):
                    if codigo:
                        locales_map[codigo] = existente
                    res_locales["actualizados"] += 1
                    print(f"    🔄 ACTUALIZADO (ID {existente})")
                else:
                    res_locales["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
            else:
                r2 = requests.post(f"{API_URL}/api/locales/", json=payload, headers=HEADERS)
                if r2.status_code in (200, 201):
                    nuevo = r2.json()
                    # Registrar tanto el código autogenerado como el del sheet
                    locales_map[nuevo["codigo"]] = nuevo["id"]
                    if codigo and codigo not in locales_map:
                        locales_map[codigo] = nuevo["id"]
                    # También actualizar por nombre para evitar duplicados
                    locales_por_nombre[nombre] = nuevo
                    res_locales["creados"] += 1
                    print(f"    ✅ CREADO (ID {nuevo['id']}, código: {nuevo['codigo']})")
                else:
                    res_locales["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
        except Exception as e:
            res_locales["fallidos"] += 1
            print(f"    ❌ {e}")

    print(f"\n   ➕ {res_locales['creados']} creados  🔄 {res_locales['actualizados']} actualizados  ❌ {res_locales['fallidos']} fallidos")
else:
    print("\n⚠️  Locales: sin datos en sheet (se usan los existentes en BD)")
    # Asegurarse de que locales_map esté cargado igual
    r = requests.get(f"{API_URL}/api/locales/", headers=HEADERS)
    locales_map = {l["codigo"]: l["id"] for l in (r.json() if r.status_code == 200 else [])}

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 6 — Sincronizar categorías
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("📂 SINCRONIZANDO CATEGORÍAS...")
print(SEP)

categoria_id_mapeo = {}  # id_sheet → id_produccion

if categorias_data:
    r = requests.get(f"{API_URL}/api/maestras/categorias", headers=HEADERS, params={"tenant_id": TENANT_ID})
    existentes = r.json() if r.status_code == 200 else []
    por_codigo = {c["codigo"]: c for c in existentes}
    print(f"   Existentes en BD: {len(existentes)}")

    for cat in categorias_data:
        id_sheet = cat.get("id", "").strip()
        codigo   = cat.get("codigo", "").strip().upper()
        nombre   = cat.get("nombre", "").strip()
        puntos   = cat.get("puntos_por_unidad", "0").strip()
        if not codigo:
            print(f"   \u26a0\ufe0f  SALTADA (falta codigo): {dict(list(cat.items())[:3])}")
            continue
        if not nombre:
            nombre = codigo  # usar codigo como nombre si nombre está vacío
            print(f"   \u26a0\ufe0f  nombre vacío para '{codigo}', se usará el codigo como nombre")

        if codigo in por_codigo:
            cat_prod = por_codigo[codigo]
            categoria_id_mapeo[id_sheet] = cat_prod["id"]
            print(f"   ℹ️  {codigo:<15} → ID {cat_prod['id']:>3} (ya existe)")
        else:
            payload = {
                "tenant_id": TENANT_ID,
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": cat.get("descripcion", "").strip() or None,
                "puntos_por_unidad": float(puntos) if puntos else 0,
            }
            r2 = requests.post(f"{API_URL}/api/maestras/categorias", json=payload, headers=HEADERS)
            if r2.status_code in (200, 201):
                nueva = r2.json()
                categoria_id_mapeo[id_sheet] = nueva["id"]
                print(f"   ✅ {codigo:<15} → ID {nueva['id']:>3} (creada)")
            else:
                print(f"   ❌ {codigo:<15} ERROR: {detalle_error(r2)}")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 7 — Importar productos
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("📦 IMPORTANDO PRODUCTOS...")
print(SEP)

# Obtener productos existentes (locales_map ya fue cargado en PASO 5.5)
r = requests.get(f"{API_URL}/api/productos/", headers=HEADERS)
productos_existentes = {p["sku"]: p for p in (r.json() if r.status_code == 200 else [])}

resultados = {"creados": [], "actualizados": [], "fallidos": []}
productos_creados = {}  # sku → id
contador = 0

for prod in productos_data:
    sku    = prod.get("sku", "").strip()
    nombre = prod.get("nombre", "").strip()
    if not sku or not nombre:
        continue

    cat_sheet_id = prod.get("categoria_id", "").strip()
    categoria_id = categoria_id_mapeo.get(cat_sheet_id)
    if cat_sheet_id and not categoria_id:
        print(f"    \u26a0\ufe0f  categoria_id '{cat_sheet_id}' no mapeada (columnas disponibles: {list(prod.keys())[:6]})")

    payload = {
        "tenant_id":         TENANT_ID,
        "nombre":            nombre,
        "sku":               sku,
        "descripcion":       prod.get("descripcion", "").strip() or None,
        "imagen_url":        prod.get("imagen_url", "").strip() or None,
        "activo":            prod.get("activo", "true").strip().lower() != "false",
        "tipo_producto_id":  int(prod["tipo_producto_id"].strip()) if prod.get("tipo_producto_id", "").strip() else 1,
        "unidad_medida_id":  int(prod["unidad_medida_id"].strip()) if prod.get("unidad_medida_id", "").strip() else 1,
        "codigo_barra":      prod.get("codigo_barra", "").strip() or None,
        "stock_minimo":      int(prod.get("stock_minimo", "0").strip() or "0"),
        "stock_critico":     int(prod.get("stock_critico", "0").strip() or "0"),
        "es_vendible":       prod.get("es_vendible", "true").strip().lower() not in ("false", "0", "no"),
        "peso_bruto":        float(prod.get("peso_bruto", "").strip()) if prod.get("peso_bruto", "").strip() else None,
    }
    # Solo incluir categoria_id si fue resuelto (evita NOT NULL violation)
    if categoria_id:
        payload["categoria_id"] = categoria_id

    print(f"\n  {sku} — {nombre}")
    try:
        if sku in productos_existentes:
            pid = productos_existentes[sku]["id"]
            r = requests.put(f"{API_URL}/api/productos/{pid}", json=payload, headers=HEADERS)
            if r.status_code in (200, 201):
                productos_creados[sku] = pid
                resultados["actualizados"].append({"sku": sku, "id": pid})
                print(f"    🔄 ACTUALIZADO (ID {pid})")
            else:
                resultados["fallidos"].append({"sku": sku, "error": detalle_error(r)})
                print(f"    ❌ {detalle_error(r)}")
        else:
            r = requests.post(f"{API_URL}/api/productos/", json=payload, headers=HEADERS)
            if r.status_code in (200, 201):
                nuevo = r.json()
                pid = nuevo["id"]
                productos_creados[sku] = pid
                resultados["creados"].append({"sku": sku, "id": pid})
                print(f"    ✅ CREADO (ID {pid})")
            else:
                resultados["fallidos"].append({"sku": sku, "error": detalle_error(r)})
                print(f"    ❌ {detalle_error(r)}")
    except Exception as e:
        resultados["fallidos"].append({"sku": sku, "error": str(e)})
        print(f"    ❌ {e}")

    contador += 1
    if contador % THROTTLE_CADA_N == 0:
        print(f"\n  ⏸️  Pausa ({contador} procesados)...")
        time.sleep(THROTTLE_SLEEP)

print(f"\n   ➕ {len(resultados['creados'])} creados  🔄 {len(resultados['actualizados'])} actualizados  ❌ {len(resultados['fallidos'])} fallidos")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 8 — Importar precios
# ═══════════════════════════════════════════════════════════════════════════════
res_precios = {"exitosos": [], "fallidos": []}
skus_faltantes_precios = set()  # SKUs en sheet de precios pero ausentes en productos

if precios_data and productos_creados:
    print(f"\n{SEP}")
    print("💰 IMPORTANDO PRECIOS...")
    print(SEP)

    r = requests.get(f"{API_URL}/api/productos/", headers=HEADERS)
    productos_full = {p["id"]: p for p in (r.json() if r.status_code == 200 else [])}

    for precio in precios_data:
        sku          = precio.get("producto_sku", "").strip()
        codigo_local = precio.get("local_codigo", "").strip()
        monto        = precio.get("monto_precio", "").strip()
        if not sku or not codigo_local or not monto:
            continue

        pid      = productos_creados.get(sku)
        local_id = locales_map.get(codigo_local)
        if not pid:
            err = f"SKU '{sku}' no en sheet de productos"
            res_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": err})
            skus_faltantes_precios.add(sku)
            continue
        if not local_id:
            print(f"    ⚠️  Local '{codigo_local}' no existe, creando...")
            local_id = get_or_create_local(codigo_local)
        if not local_id:
            err = f"Local '{codigo_local}' no existe y no se pudo crear"
            res_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": err})
            print(f"    ❌ {err}")
            continue

        prod_full = productos_full.get(pid)
        if not prod_full or not prod_full.get("unidad_medida_id"):
            err = f"Sin unidad_medida_id para producto {pid} ({sku})"
            res_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": err})
            print(f"    ❌ {err}")
            continue

        uid = prod_full["unidad_medida_id"]
        print(f"\n  {sku} / {codigo_local}: ${monto}")
        try:
            r = requests.put(
                f"{API_URL}/api/precios/producto/{pid}/local/{local_id}/unidad/{uid}",
                json={"monto_precio": float(monto)},
                headers=HEADERS,
            )
            if r.status_code in (200, 201):
                res_precios["exitosos"].append({"sku": sku, "local": codigo_local})
                print("    ✅ OK")
            else:
                res_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": detalle_error(r)})
                print(f"    ❌ {detalle_error(r)}")
        except Exception as e:
            res_precios["fallidos"].append({"sku": sku, "local": codigo_local, "error": str(e)})
            print(f"    ❌ {e}")

    print(f"\n   ✅ {len(res_precios['exitosos'])} precios  ❌ {len(res_precios['fallidos'])} fallidos")
    if skus_faltantes_precios:
        print(f"   ⚠️  SKUs referenciados en precios pero ausentes en sheet de productos: {', '.join(sorted(skus_faltantes_precios))}")
else:
    print("\n⚠️  Precios: saltados (sin datos o sin productos importados)")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 9 — Importar inventario
# ═══════════════════════════════════════════════════════════════════════════════
res_inventario = {"exitosos": [], "fallidos": []}
skus_faltantes_inventario = set()  # SKUs en sheet de inventario pero ausentes en productos

if inventario_data and productos_creados:
    print(f"\n{SEP}")
    print("📊 IMPORTANDO INVENTARIO...")
    print(SEP)

    for inv in inventario_data:
        sku          = inv.get("producto_sku", "").strip()
        codigo_local = inv.get("local_codigo", "").strip()
        cantidad     = inv.get("cantidad_stock", "").strip()
        if not sku or not codigo_local or not cantidad:
            continue

        pid      = productos_creados.get(sku)
        local_id = locales_map.get(codigo_local)
        if not pid:
            err = f"SKU '{sku}' no en sheet de productos"
            res_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": err})
            skus_faltantes_inventario.add(sku)
            continue
        if not local_id:
            local_id = locales_map.get(codigo_local)  # puede haber sido creado en paso precios
            if not local_id:
                print(f"    ⚠️  Local '{codigo_local}' no existe, creando...")
                local_id = get_or_create_local(codigo_local)
        if not local_id:
            err = f"Local '{codigo_local}' no existe y no se pudo crear"
            res_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": err})
            print(f"    ❌ {err}")
            continue

        print(f"\n  {sku} / {codigo_local}: {cantidad} uds.")
        try:
            r = requests.put(
                f"{API_URL}/api/inventario/producto/{pid}/local/{local_id}",
                json={"cantidad_stock": int(cantidad)},
                headers=HEADERS,
            )
            if r.status_code in (200, 201):
                res_inventario["exitosos"].append({"sku": sku, "local": codigo_local})
                print("    ✅ OK")
            else:
                res_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": detalle_error(r)})
                print(f"    ❌ {detalle_error(r)}")
        except Exception as e:
            res_inventario["fallidos"].append({"sku": sku, "local": codigo_local, "error": str(e)})
            print(f"    ❌ {e}")

    print(f"\n   ✅ {len(res_inventario['exitosos'])} inventarios  ❌ {len(res_inventario['fallidos'])} fallidos")
    if skus_faltantes_inventario:
        print(f"   ⚠️  SKUs referenciados en inventario pero ausentes en sheet de productos: {', '.join(sorted(skus_faltantes_inventario))}")
else:
    print("\n⚠️  Inventario: saltado (sin datos o sin productos importados)")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 10 — Sincronizar tipos de proveedor
# ═══════════════════════════════════════════════════════════════════════════════
res_tipos_proveedor = {"creados": 0, "actualizados": 0, "fallidos": 0}
tipos_proveedor_map = {}  # codigo → id

if tipos_proveedor_data:
    print(f"\n{SEP}")
    print("🏷️  SINCRONIZANDO TIPOS DE PROVEEDOR...")
    print(SEP)

    r = requests.get(f"{API_URL}/api/maestras/tipos-proveedor", headers=HEADERS)
    existentes_tp = {tp["codigo"]: tp for tp in (r.json() if r.status_code == 200 else [])}
    # Detectar si la hoja tipos_proveedor no existe (Google devuelve prod. por defecto)
    if tipos_proveedor_data and "sku" in tipos_proveedor_data[0] and "codigo" not in tipos_proveedor_data[0]:
        print("   \u26a0\ufe0f  El tab 'tipos_proveedor' no existe en el Sheet o tiene columnas incorrectas.")
        print("   \u26a0\ufe0f  Se esperan columnas: codigo, nombre, descripcion, activo")
        tipos_proveedor_data = []
    for tp in tipos_proveedor_data:
        codigo = tp.get("codigo", "").strip().upper()
        nombre = tp.get("nombre", "").strip()
        if not codigo or not nombre:
            print(f"   ⚠️  SALTADO (falta codigo o nombre): {dict(list(tp.items())[:3])}")
            continue

        descripcion = tp.get("descripcion", "").strip() or None
        activo_str  = tp.get("activo", "true").strip().lower()
        activo      = activo_str not in ("false", "0", "no")

        print(f"\n  {codigo} — {nombre}")
        if codigo in existentes_tp:
            existing = existentes_tp[codigo]
            tipos_proveedor_map[codigo] = existing["id"]
            # Actualizar si hay cambios en nombre/descripcion
            payload_upd = {"nombre": nombre, "activo": activo}
            if descripcion is not None:
                payload_upd["descripcion"] = descripcion
            r2 = requests.put(
                f"{API_URL}/api/maestras/tipos-proveedor/{existing['id']}",
                json=payload_upd,
                headers=HEADERS,
            )
            if r2.status_code in (200, 201):
                res_tipos_proveedor["actualizados"] += 1
                print(f"    🔄 ACTUALIZADO (ID {existing['id']})")
            else:
                res_tipos_proveedor["fallidos"] += 1
                print(f"    ❌ {detalle_error(r2)}")
        else:
            payload = {"codigo": codigo, "nombre": nombre, "activo": activo}
            if descripcion is not None:
                payload["descripcion"] = descripcion
            r2 = requests.post(f"{API_URL}/api/maestras/tipos-proveedor", json=payload, headers=HEADERS)
            if r2.status_code in (200, 201):
                nuevo = r2.json()
                tipos_proveedor_map[codigo] = nuevo["id"]
                res_tipos_proveedor["creados"] += 1
                print(f"    ✅ CREADO (ID {nuevo['id']})")
            else:
                res_tipos_proveedor["fallidos"] += 1
                print(f"    ❌ {detalle_error(r2)}")

    print(f"\n   ➕ {res_tipos_proveedor['creados']} creados  🔄 {res_tipos_proveedor['actualizados']} actualizados  ❌ {res_tipos_proveedor['fallidos']} fallidos")
else:
    print("\n⚠️  Tipos de proveedor: saltados (hoja vacía o no encontrada)")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 11 — Sincronizar proveedores
# ═══════════════════════════════════════════════════════════════════════════════
res_proveedores = {"creados": 0, "actualizados": 0, "fallidos": 0}
proveedores_map = {}  # rut → id  (fallback: nombre → id)

if proveedores_data:
    # Detectar si el tab 'proveedores' no existe (Google devuelve prod. por defecto)
    if "sku" in proveedores_data[0] and "nombre" in proveedores_data[0] and "rut" not in proveedores_data[0]:
        print("\n⚠️  El tab 'proveedores' no existe en el Sheet o tiene columnas incorrectas.")
        print("   Se esperan columnas: nombre, rut, contacto, email, tipo_proveedor_codigo, activo")
        proveedores_data = []

if proveedores_data:
    print(f"\n{SEP}")
    print("🚚 SINCRONIZANDO PROVEEDORES...")
    print(SEP)

    r = requests.get(f"{API_URL}/api/compras/proveedores", headers=HEADERS)
    existentes_pv = r.json() if r.status_code == 200 else []
    por_rut    = {p["rut"]: p for p in existentes_pv if p.get("rut")}
    por_nombre = {p["nombre"]: p for p in existentes_pv}

    # Si tipos_proveedor_map está vacío (hoja omitida), cargar desde API
    if not tipos_proveedor_map:
        r_tp = requests.get(f"{API_URL}/api/maestras/tipos-proveedor", headers=HEADERS)
        for tp in (r_tp.json() if r_tp.status_code == 200 else []):
            tipos_proveedor_map[tp["codigo"]] = tp["id"]

    for pv in proveedores_data:
        nombre = pv.get("nombre", "").strip()
        if not nombre:
            print(f"   ⚠️  SALTADO (falta nombre): {dict(list(pv.items())[:3])}")
            continue

        rut       = pv.get("rut", "").strip() or None
        contacto  = pv.get("contacto", "").strip() or None
        email     = pv.get("email", "").strip() or None
        telefono  = pv.get("telefono", "").strip() or None
        direccion = pv.get("direccion", "").strip() or None
        activo_str = pv.get("activo", "true").strip().lower()
        activo    = activo_str not in ("false", "0", "no")

        # Resolver tipo_proveedor_id: primero por codigo, luego por ID directo
        tipo_cod = pv.get("tipo_proveedor_codigo", "").strip().upper()
        tipo_id_directo_str = pv.get("tipo_proveedor_id", "").strip()
        tipo_proveedor_id = tipos_proveedor_map.get(tipo_cod) if tipo_cod else None
        if not tipo_proveedor_id and tipo_id_directo_str.isdigit():
            tipo_proveedor_id = int(tipo_id_directo_str)
        if tipo_cod and not tipo_proveedor_id:
            print(f"   ⚠️  tipo_proveedor_codigo '{tipo_cod}' no encontrado para '{nombre}'")

        payload = {
            "nombre":            nombre,
            "activo":            activo,
        }
        if rut:
            payload["rut"] = rut
        if contacto:
            payload["contacto"] = contacto
        if email:
            payload["email"] = email
        if telefono:
            payload["telefono"] = telefono
        if direccion:
            payload["direccion"] = direccion
        if tipo_proveedor_id:
            payload["tipo_proveedor_id"] = tipo_proveedor_id

        print(f"\n  {nombre}" + (f" (RUT: {rut})" if rut else ""))

        # Determinar si ya existe: primero por RUT, después por nombre
        existente = por_rut.get(rut) if rut else None
        if not existente:
            existente = por_nombre.get(nombre)

        try:
            if existente:
                pid = existente["id"]
                r2 = requests.put(f"{API_URL}/api/compras/proveedores/{pid}", json=payload, headers=HEADERS)
                if r2.status_code in (200, 201):
                    llave = rut or nombre
                    proveedores_map[llave] = pid
                    res_proveedores["actualizados"] += 1
                    print(f"    🔄 ACTUALIZADO (ID {pid})")
                else:
                    res_proveedores["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
            else:
                r2 = requests.post(f"{API_URL}/api/compras/proveedores", json=payload, headers=HEADERS)
                if r2.status_code in (200, 201):
                    nuevo = r2.json()
                    pid = nuevo["id"]
                    llave = rut or nombre
                    proveedores_map[llave] = pid
                    res_proveedores["creados"] += 1
                    print(f"    ✅ CREADO (ID {pid})")
                else:
                    res_proveedores["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
        except Exception as e:
            res_proveedores["fallidos"] += 1
            print(f"    ❌ {e}")

    print(f"\n   ➕ {res_proveedores['creados']} creados  🔄 {res_proveedores['actualizados']} actualizados  ❌ {res_proveedores['fallidos']} fallidos")
else:
    print("\n⚠️  Proveedores: saltados (hoja vacía o no encontrada)")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 12 — Sincronizar precios de proveedor
# ═══════════════════════════════════════════════════════════════════════════════
res_precios_proveedor = {"creados": 0, "actualizados": 0, "fallidos": 0}

if precios_proveedor_data and productos_creados:
    print(f"\n{SEP}")
    print("💲 SINCRONIZANDO PRECIOS DE PROVEEDOR...")
    print(SEP)

    # Si proveedores_map está vacío (hoja omitida), cargar desde API
    if not proveedores_map:
        r_pv = requests.get(f"{API_URL}/api/compras/proveedores", headers=HEADERS)
        for p in (r_pv.json() if r_pv.status_code == 200 else []):
            if p.get("rut"):
                proveedores_map[p["rut"]] = p["id"]
            proveedores_map[p["nombre"]] = p["id"]

    # Cargar precios existentes indexados por (producto_id, proveedor_id)
    r_pp = requests.get(
        f"{API_URL}/api/precios-proveedor/",
        headers=HEADERS,
        params={"solo_activos": "false", "limit": 10000},
    )
    existentes_pp = {}
    for pp in (r_pp.json() if r_pp.status_code == 200 else []):
        existentes_pp[(pp["producto_id"], pp["proveedor_id"])] = pp["id"]

    for pp in precios_proveedor_data:
        # Acepta 'producto_sku' o 'producto_id' como columna del SKU
        sku          = pp.get("producto_sku", "").strip() or pp.get("producto_id", "").strip()
        pv_rut       = pp.get("proveedor_rut", "").strip() or None
        pv_nombre    = pp.get("proveedor_nombre", "").strip() or None
        # ID directo del proveedor (columna 'proveedor_id' con valor numérico)
        pv_id_directo_str = pp.get("proveedor_id", "").strip()
        pv_id_directo = int(pv_id_directo_str) if pv_id_directo_str.isdigit() else None
        # Acepta tanto 'precio_kg' como el typo 'percio_kg'
        precio_kg    = pp.get("precio_kg", "").strip() or pp.get("percio_kg", "").strip()
        notas        = pp.get("notas", "").strip() or None
        activo_str   = pp.get("activo", "true").strip().lower()
        activo       = activo_str not in ("false", "0", "no")

        if not sku or not precio_kg:
            print(f"   ⚠️  SALTADO (falta sku o precio_kg): {dict(list(pp.items())[:4])}")
            continue

        # Resolver producto_id
        producto_id = productos_creados.get(sku)
        if not producto_id:
            res_precios_proveedor["fallidos"] += 1
            print(f"   ❌ SKU '{sku}' no importado en este run")
            continue

        # Resolver proveedor_id: RUT > nombre > ID directo (solo si pertenece al tenant) > único proveedor
        # Los IDs válidos son SOLO los del tenant actual (proveedores_map.values())
        ids_validos_tenant = set(proveedores_map.values())
        proveedor_id = None
        if pv_rut:
            proveedor_id = proveedores_map.get(pv_rut)
        if not proveedor_id and pv_nombre:
            proveedor_id = proveedores_map.get(pv_nombre)
        if not proveedor_id and pv_id_directo:
            # Solo aceptar ID directo si pertenece al tenant actual (evita cross-tenant)
            if pv_id_directo in ids_validos_tenant:
                proveedor_id = pv_id_directo
            # Si el ID no pertenece al tenant pero hay UN SOLO proveedor, usarlo automáticamente
            elif len(ids_validos_tenant) == 1:
                proveedor_id = next(iter(ids_validos_tenant))
                print(f"   ℹ️  proveedor_id={pv_id_directo} no pertenece al tenant → usando único proveedor disponible (ID {proveedor_id})")
            else:
                res_precios_proveedor["fallidos"] += 1
                print(f"   ❌ proveedor_id={pv_id_directo} no pertenece al tenant actual (IDs válidos: {sorted(ids_validos_tenant)})")
                continue
        # Fallback final: si hay exactamente un proveedor en el tenant, usarlo
        if not proveedor_id and len(ids_validos_tenant) == 1:
            proveedor_id = next(iter(ids_validos_tenant))
            print(f"   ℹ️  Sin proveedor especificado → usando único proveedor disponible (ID {proveedor_id})")
        if not proveedor_id:
            res_precios_proveedor["fallidos"] += 1
            key = pv_rut or pv_nombre or pv_id_directo_str or "???"
            print(f"   ❌ Proveedor '{key}' no encontrado para SKU '{sku}'")
            continue

        print(f"\n  {sku} / proveedor {proveedor_id}: ${precio_kg}/kg")
        try:
            clave = (producto_id, proveedor_id)
            if clave in existentes_pp:
                pp_id = existentes_pp[clave]
                payload_upd = {"precio_kg": float(precio_kg)}
                if notas is not None:
                    payload_upd["notas"] = notas
                r2 = requests.put(
                    f"{API_URL}/api/precios-proveedor/{pp_id}",
                    json=payload_upd,
                    headers=HEADERS,
                )
                if r2.status_code in (200, 201):
                    res_precios_proveedor["actualizados"] += 1
                    print(f"    🔄 ACTUALIZADO (ID {pp_id})")
                else:
                    res_precios_proveedor["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
            else:
                payload = {
                    "producto_id":  producto_id,
                    "proveedor_id": proveedor_id,
                    "precio_kg":    float(precio_kg),
                    "activo":       activo,
                }
                if notas is not None:
                    payload["notas"] = notas
                r2 = requests.post(f"{API_URL}/api/precios-proveedor/", json=payload, headers=HEADERS)
                if r2.status_code in (200, 201):
                    nuevo = r2.json()
                    existentes_pp[clave] = nuevo["id"]
                    res_precios_proveedor["creados"] += 1
                    print(f"    ✅ CREADO (ID {nuevo['id']})")
                else:
                    res_precios_proveedor["fallidos"] += 1
                    print(f"    ❌ {detalle_error(r2)}")
        except Exception as e:
            res_precios_proveedor["fallidos"] += 1
            print(f"    ❌ {e}")

    print(f"\n   ➕ {res_precios_proveedor['creados']} creados  🔄 {res_precios_proveedor['actualizados']} actualizados  ❌ {res_precios_proveedor['fallidos']} fallidos")
else:
    print("\n⚠️  Precios proveedor: saltados (sin datos o sin productos importados)")

# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("📊 RESUMEN FINAL")
print(SEP)
print(f"   Entorno:    {ENV['label']}")
print(f"   Tenant:     [{TENANT_ID}] {TENANT['nombre']}")
print(f"   Sheet:      {SHEET_ID}")
print()
print(f"   🏪 Locales:            ➕ {res_locales['creados']:>3}   🔄 {res_locales['actualizados']:>3}   ❌ {res_locales['fallidos']:>3}")
print(f"   📦 Productos:          ➕ {len(resultados['creados']):>3} nuevos   🔄 {len(resultados['actualizados']):>3} actualizados   ❌ {len(resultados['fallidos']):>3} fallidos")
print(f"   💰 Precios:            ✅ {len(res_precios['exitosos']):>3}   ❌ {len(res_precios['fallidos']):>3}")
print(f"   📊 Inventario:         ✅ {len(res_inventario['exitosos']):>3}   ❌ {len(res_inventario['fallidos']):>3}")
print(f"   🏷️  Tipos proveedor:   ➕ {res_tipos_proveedor['creados']:>3}   🔄 {res_tipos_proveedor['actualizados']:>3}   ❌ {res_tipos_proveedor['fallidos']:>3}")
print(f"   🚚 Proveedores:        ➕ {res_proveedores['creados']:>3}   🔄 {res_proveedores['actualizados']:>3}   ❌ {res_proveedores['fallidos']:>3}")
print(f"   💲 Precios proveedor:  ➕ {res_precios_proveedor['creados']:>3}   🔄 {res_precios_proveedor['actualizados']:>3}   ❌ {res_precios_proveedor['fallidos']:>3}")

if resultados["creados"]:
    print("\n   ➕ Productos nuevos:")
    for p in resultados["creados"]:
        print(f"      • {p['sku']:<15} (ID {p['id']})")

if resultados["fallidos"]:
    print("\n   ❌ Fallidos:")
    for p in resultados["fallidos"]:
        print(f"      • {p['sku']:<15} — {p['error']}")

skus_huerfanos = skus_faltantes_precios | skus_faltantes_inventario
if skus_huerfanos:
    print(f"\n   ⚠️  SKUs huérfanos (en precios/inventario pero NO en sheet 'productos'):")
    for sku in sorted(skus_huerfanos):
        en = []
        if sku in skus_faltantes_precios:
            en.append("precios")
        if sku in skus_faltantes_inventario:
            en.append("inventario")
        print(f"      • {sku:<15} — referenciado en: {', '.join(en)}")
    print(f"\n      👉 Agregar estos SKUs a la hoja 'productos' del Google Sheet y re-sincronizar.")

print(f"\n{SEP}")
print("🎯 SINCRONIZACIÓN COMPLETADA")
print(SEP)
