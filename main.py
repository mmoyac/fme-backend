"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.auth import get_current_active_user

# Importar routers
from routers import inventario, productos, locales, precios, pedidos, movimientos_inventario, clientes, dashboard, auth, admin_users, admin_utils, payments, test_payments, maestras, recetas, produccion, compras, cheques, puntos, caja, enrolamiento, gemini_vision, precios_proveedor, stock_cajas, alertas, tipos_pedido, despachos, configuracion, debug_menu, admin_configuracion_landing, tenants, etiquetas, paleta_colores, solicitudes_transferencia, locales_cliente, preventa, hojas_ruta, vehiculos


app = FastAPI(
    title="FME Backend API",
    description="API para el sistema FME - Consulta de Inventario",
    version="1.0.0"
)

# Configuración de CORS
origins = [
    # Producción
    "https://masasestacion.cl",
    "https://www.masasestacion.cl",
    "https://elolivo.masasestacion.cl",
    "https://api.masasestacion.cl",
    "https://admin.masasestacion.cl",
    "https://backoffice.masasestacion.cl",
    # Producción lexastech.cl (tenants)
    "https://elolivo.lexastech.cl",
    "https://admin.elolivo.lexastech.cl",
    "https://bigschool.lexastech.cl",
    "https://admin.bigschool.lexastech.cl",
    "https://elquincho.lexastech.cl",
    "https://admin.elquincho.lexastech.cl",
    
    # Desarrollo local (localhost)
    "http://localhost:3000",  # Landing en desarrollo
    "http://localhost:3001",  # Backoffice en desarrollo
    "http://localhost:8080",
    "http://localhost",       # POS App (Capacitor Android)
    
    # Desarrollo local (hosts file)
    "http://masasestacion.local:3000",
    "http://masasestacion.local:3001",
    "http://elolivo.local:3000",
    "http://elolivo.local:3001",
    "http://donajuanita.local:3000",
    "http://donajuanita.local:3001",
    "http://api.masasestacion.local:8000",
    "http://admin.masasestacion.local:3001",
    "http://admin.elolivo.local:3001",
    "http://admin.donajuanita.local:3001",
    
    # POS App (Capacitor)
    "capacitor://localhost",  # POS App (Capacitor iOS)
    "ionic://localhost",      # POS App (Capacitor alternativo)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
