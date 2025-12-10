"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.auth import get_current_active_user

# Importar routers
# Importar routers
from routers import inventario, productos, locales, precios, pedidos, movimientos_inventario, clientes, dashboard, auth, admin_users, payments, test_payments, maestras, recetas

app = FastAPI(
    title="FME Backend API",
    description="API para el sistema FME - Consulta de Inventario",
    version="1.0.0"
)

# Configuración de CORS
origins = [
    "https://masasestacion.cl",
    "https://www.masasestacion.cl",
    "https://backoffice.masasestacion.cl",
    "https://admin.masasestacion.cl",
    "http://localhost:3000",  # Landing en desarrollo
    "http://localhost:3001",  # Backoffice en desarrollo
    "http://localhost:8080",
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

# Registrar routers
# Registrar routers (Secured globally where applicable)
app.include_router(inventario.router, prefix="/api/inventario", tags=["Inventario"], dependencies=[Depends(get_current_active_user)])
app.include_router(productos.router, prefix="/api/productos", tags=["Productos"]) # Mixed content, auth handled inside
app.include_router(locales.router, prefix="/api/locales", tags=["Locales"], dependencies=[Depends(get_current_active_user)])
app.include_router(precios.router, prefix="/api/precios", tags=["Precios"], dependencies=[Depends(get_current_active_user)])
app.include_router(pedidos.router, prefix="/api/pedidos", tags=["Pedidos"]) # Mixed content, auth handled inside
app.include_router(movimientos_inventario.router, prefix="/api/movimientos", tags=["Movimientos"], dependencies=[Depends(get_current_active_user)])
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"], dependencies=[Depends(get_current_active_user)])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_active_user)])
app.include_router(admin_users.router, prefix="/api/admin", tags=["Administración Usuarios"])
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(payments.router, prefix="/api/payments", tags=["Pagos"])
app.include_router(test_payments.router, prefix="/api/test", tags=["⚠️ TEST ONLY - ELIMINAR EN PRODUCCIÓN"])
app.include_router(maestras.router, prefix="/api/maestras", tags=["Tablas Maestras"], dependencies=[Depends(get_current_active_user)])
app.include_router(recetas.router, prefix="/api/recetas", tags=["Recetas"], dependencies=[Depends(get_current_active_user)])

@app.get("/")
async def root():
    """Endpoint de bienvenida."""
    return {"message": "Bienvenido a FME Backend API"}

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud."""
    return {"status": "healthy"}
