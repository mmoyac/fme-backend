"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware  # noqa: F401 (kept for potential use)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from routers.auth import get_current_active_user

# Importar routers
from routers import inventario, productos, locales, precios, pedidos, movimientos_inventario, clientes, dashboard, auth, admin_users, admin_utils, payments, test_payments, maestras, recetas, produccion, compras, cheques, puntos, caja, enrolamiento, gemini_vision, precios_proveedor, stock_cajas, alertas, tipos_pedido, despachos, configuracion, debug_menu, admin_configuracion_landing, tenants, etiquetas, paleta_colores, solicitudes_transferencia, locales_cliente, preventa, hojas_ruta, vehiculos, comisiones


app = FastAPI(
    title="FME Backend API",
    description="API para el sistema FME - Consulta de Inventario",
    version="1.0.0"
)

# Orígenes estáticos siempre permitidos (desarrollo + apps móviles)
STATIC_ORIGINS = [
    # Producción masasestacion.cl
    "https://masasestacion.cl",
    "https://www.masasestacion.cl",
    "https://api.masasestacion.cl",
    "https://admin.masasestacion.cl",
    # Desarrollo local (localhost)
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8080",
    "http://localhost",
    # POS App (Capacitor)
    "capacitor://localhost",
    "ionic://localhost",
]


def get_allowed_origins() -> list[str]:
    """
    Construye la lista de orígenes CORS combinando los estáticos
    con los dominios de todos los tenants registrados en la BD.
    Genera automáticamente para cada tenant:
    - http://{subdomain}.local:3000 / :3001  (desarrollo)
    - https://{dominio_principal}            (producción)
    """
    from database.database import SessionLocal
    from database.models import Tenant
    origins = list(STATIC_ORIGINS)
    try:
        db = SessionLocal()
        tenants = db.query(Tenant).filter(Tenant.activo == True).all()
        for tenant in tenants:
            # Orígenes de desarrollo .local desde subdomain
            if tenant.subdomain:
                s = tenant.subdomain.strip()
                for port in [3000, 3001, 8080]:
                    origins.append(f"http://{s}.local:{port}")
                    origins.append(f"http://admin.{s}.local:{port}")
                origins.append(f"http://{s}.local")
            # Orígenes de producción desde dominio_principal
            if tenant.dominio_principal:
                d = tenant.dominio_principal.strip()
                origins.append(f"https://{d}")
                origins.append(f"https://www.{d}")
                origins.append(f"https://admin.{d}")
        db.close()
    except Exception:
        pass  # Si la BD no está lista aún, usamos solo los estáticos
    return list(set(origins))


def is_origin_allowed(origin: str, allowed: list[str]) -> bool:
    """Verifica si un origen está permitido. Acepta comodín *.local en desarrollo."""
    if origin in allowed:
        return True
    # Comodín de desarrollo: cualquier *.local (cualquier puerto)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        if parsed.scheme == "http" and parsed.hostname and parsed.hostname.endswith(".local"):
            return True
    except Exception:
        pass
    return False


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware CORS dinámico: valida el Origin contra BD en cada petición.
    Permite agregar nuevos tenants sin redesplegar.
    """
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        allowed = get_allowed_origins()

        if request.method == "OPTIONS":
            if is_origin_allowed(origin, allowed):
                return Response(
                    status_code=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Max-Age": "600",
                    },
                )
            return Response(status_code=400)

        response = await call_next(request)
        if is_origin_allowed(origin, allowed):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


app.add_middleware(DynamicCORSMiddleware)

# Servir archivos estáticos (imágenes de productos)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Endpoint de health check ligero (sin dependencias pesadas)
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint ultra ligero para health checks.
    No requiere autenticación ni consultas a BD.
    Responde en < 5ms.
    """
    return {"status": "ok", "service": "fme-backend"}

# Registrar routers
app.include_router(inventario.router, prefix="/api/inventario", tags=["Inventario"], dependencies=[Depends(get_current_active_user)])
app.include_router(productos.router, prefix="/api/productos", tags=["Productos"])
app.include_router(locales.router, prefix="/api/locales", tags=["Locales"], dependencies=[Depends(get_current_active_user)])
app.include_router(precios.router, prefix="/api/precios", tags=["Precios"], dependencies=[Depends(get_current_active_user)])
app.include_router(pedidos.router, prefix="/api/pedidos", tags=["Pedidos"])
app.include_router(movimientos_inventario.router, prefix="/api/movimientos", tags=["Movimientos"], dependencies=[Depends(get_current_active_user)])
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"], dependencies=[Depends(get_current_active_user)])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_active_user)])
app.include_router(admin_users.router, prefix="/api/admin", tags=["Administración Usuarios"])
app.include_router(admin_utils.router, prefix="/api/admin", tags=["Utilidades Admin"], dependencies=[Depends(get_current_active_user)])
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(payments.router, prefix="/api/payments", tags=["Pagos"])
app.include_router(test_payments.router, prefix="/api/test", tags=["⚠️ TEST ONLY - ELIMINAR EN PRODUCCIÓN"])
app.include_router(maestras.router, prefix="/api/maestras", tags=["Tablas Maestras"], dependencies=[Depends(get_current_active_user)])
app.include_router(recetas.router, prefix="/api/recetas", tags=["Recetas"], dependencies=[Depends(get_current_active_user)])
app.include_router(produccion.router, prefix="/api", tags=["Producción"])
app.include_router(compras.router, prefix="/api", tags=["Compras"], dependencies=[Depends(get_current_active_user)])
app.include_router(cheques.router, prefix="/api/cheques", tags=["Cheques"], dependencies=[Depends(get_current_active_user)])
app.include_router(puntos.router, tags=["Puntos"])
app.include_router(caja.router, prefix="/api/caja", tags=["Caja"], dependencies=[Depends(get_current_active_user)])
app.include_router(tipos_pedido.router, prefix="/api/tipos-pedido", tags=["Tipos de Pedido"])
app.include_router(enrolamiento.router, prefix="/api/enrolamiento", tags=["Enrolamiento WMS"], dependencies=[Depends(get_current_active_user)])
app.include_router(preventa.router, prefix="/api/preventa", tags=["Pre-Venta Cajas"], dependencies=[Depends(get_current_active_user)])
app.include_router(preventa.router_pdf, prefix="/api/preventa", tags=["Pre-Venta Cajas PDF"])
app.include_router(gemini_vision.router, tags=["Gemini Vision"], dependencies=[Depends(get_current_active_user)])
app.include_router(precios_proveedor.router, prefix="/api/precios-proveedor", tags=["Precios Proveedor"], dependencies=[Depends(get_current_active_user)])
app.include_router(stock_cajas.router, prefix="/api/stock-cajas", tags=["Stock Cajas"], dependencies=[Depends(get_current_active_user)])
app.include_router(alertas.router, prefix="/api/alertas", tags=["Alertas"], dependencies=[Depends(get_current_active_user)])
app.include_router(despachos.router, prefix="/api/despachos", tags=["Despachos"], dependencies=[Depends(get_current_active_user)])
app.include_router(configuracion.router, prefix="/api/config", tags=["Configuración"])
app.include_router(admin_configuracion_landing.router, prefix="/api/admin/configuracion-landing", tags=["Admin - Configuración Landing"], dependencies=[Depends(get_current_active_user)])
app.include_router(tenants.router, prefix="/api/tenants", tags=["Tenants (Multi-tenant SaaS)"])
app.include_router(etiquetas.router, tags=["Etiquetas"], dependencies=[Depends(get_current_active_user)])
app.include_router(paleta_colores.router, prefix="/api/paleta-colores", tags=["Paletas de Colores"], dependencies=[Depends(get_current_active_user)])
app.include_router(debug_menu.router, prefix="/api/debug", tags=["Debug Menu"])

# Registrar router de locales_cliente (locales propios de cliente)
app.include_router(locales_cliente.router)

# Registrar router de solicitudes de transferencia
app.include_router(solicitudes_transferencia.router)
app.include_router(comisiones.router, prefix="/api/comisiones", tags=["Comisiones Vendedores"], dependencies=[Depends(get_current_active_user)])

# Registrar router de hojas de ruta
app.include_router(hojas_ruta.router)
app.include_router(vehiculos.router, dependencies=[Depends(get_current_active_user)])

@app.get("/")
async def root():
    """Endpoint de bienvenida."""
    return {"message": "Bienvenido a FME Backend API"}

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud."""
    return {"status": "healthy"}
