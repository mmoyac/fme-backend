# 🚀 FME Backend - Masas Estación

API REST para e-commerce de Masas Estación, construida con FastAPI, SQLAlchemy y PostgreSQL.

## ✨ Características

- ⚡ **FastAPI** - Framework moderno y rápido para APIs
- 🗄️ **PostgreSQL** - Base de datos relacional robusta
- 🔄 **SQLAlchemy 2.0** - ORM con soporte completo de tipos
- 🐳 **Docker** - Despliegue containerizado
- 📝 **Alembic** - Migraciones de base de datos
- 📚 **OpenAPI/Swagger** - Documentación automática
- 🎯 **Pydantic** - Validación de datos
- 🏆 **Sistema de Puntos** - Fidelización completa por categorías
- 🔐 **JWT Auth** - Autenticación y autorización
- ✅ **32 Tests** - Suite completa de tests automatizados

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose instalados
- Python 3.11+ (para desarrollo local)

### Configuración con Docker

1. Clonar el repositorio y navegar al directorio:
```bash
cd fme-backend
```

2. Copiar el archivo de variables de entorno (ya existe `.env` en el proyecto):
```bash
# El archivo .env ya está configurado con valores por defecto
```

3. Iniciar los servicios con Docker Compose:
```bash
docker-compose up -d
```

4. La API estará disponible en: http://localhost:8000
   - Documentación Swagger: http://localhost:8000/docs
   - Documentación ReDoc: http://localhost:8000/redoc

### Desarrollo Local (sin Docker)

1. Crear entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar `.env` con la URL de PostgreSQL local

4. Iniciar el servidor:
```bash
uvicorn main:app --reload
```

## 📁 Estructura del Proyecto

```
fme-backend/
├── main.py                 # Punto de entrada FastAPI
├── routers/                # Endpoints de la API
│   ├── inventario.py      # Consultas de inventario
│   └── productos.py       # Catálogo de productos
├── schemas/                # Modelos Pydantic (validación)
│   ├── producto.py
│   ├── inventario_consulta.py
│   └── catalogo.py
├── database/               # Capa de datos
│   ├── database.py        # Configuración SQLAlchemy
│   └── models.py          # Modelos ORM (7 tablas)
├── services/               # Lógica de negocio
│   └── inventario_service.py
├── scripts/                # Scripts de carga de datos
│   ├── load_productos.py
│   ├── load_locales.py
│   └── load_inventario_inicial.py
├── migrations/             # Migraciones Alembic
│   └── versions/
├── tests/                  # Tests unitarios
├── docs/                   # CSV de datos iniciales
├── requirements.txt        # Dependencias Python
├── Dockerfile
├── docker-compose.yml
├── .env                    # Variables de entorno
└── AGENTS.md              # Guía para agentes de IA
```

## 🗄️ Modelo de Datos

### Tablas Principales

| Tabla | Descripción | Campos Clave |
|-------|-------------|--------------|
| `productos` | Catálogo de productos | id, sku, nombre, descripcion |
| `locales` | Sucursales y punto web | id, codigo (LAMPA/TILTIL/WEB), nombre, direccion |
| `inventario` | Stock por producto/local | producto_id, local_id, cantidad_stock |
| `precios` | Precio por producto/local | producto_id, local_id, monto_precio |
| `clientes` | Base de clientes | id, nombre, email, telefono |
| `pedidos` | Órdenes de compra | id, cliente_id, fecha_pedido, estado, puntos_ganados |
| `items_pedido` | Detalle de pedidos | pedido_id, producto_id, cantidad, precio_unitario |
| `puntos_cliente` | Estado puntos fidelización | cliente_id, puntos_disponibles, puntos_totales_ganados |
| `movimientos_puntos` | Historial de puntos | cliente_id, pedido_id, tipo_movimiento, puntos |

### Relaciones

```
productos ─┬─ inventario (1:N) ─ locales
           ├─ precios (1:N) ─ locales
           └─ items_pedido (1:N)

clientes ─ pedidos (1:N) ─ items_pedido (1:N)
```

## 🔌 API Endpoints

### Inventario

**GET** `/api/inventario/resumen`
- Lista todos los productos con stock total agregado
- Response: `List[InventarioResumen]`

**GET** `/api/inventario/detalle/{sku}`
- Stock detallado por local para un producto
- Response: `InventarioDetalle`

### Productos

**GET** `/api/productos/catalogo`
- Catálogo web con precios del local "WEB"
- Incluye stock total y descripción
- Incluye información de puntos de fidelización por categoría
- Response: `List[ProductoCatalogo]`

### Puntos de Fidelización

**GET** `/api/clientes/{id}`
- Información completa del cliente incluyendo puntos
- Response: `ClienteConPuntos`

**POST** `/api/pedidos/`
- Crear pedido con cálculo automático de puntos
- Otorga puntos según categoría de productos

**PUT** `/api/pedidos/{id}`
- Confirmar/cancelar pedido con gestión automática de puntos

### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Comandos Útiles

### Docker
```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Detener servicios
docker-compose down

# Reconstruir imágenes
docker-compose up --build
```

### Base de Datos

> ⚠️ **IMPORTANTE: Sincronización de Base de Datos**
> Si modificas los modelos en `models.py` (agregas tablas o columnas), DEBES:
> 1. Crear una nueva migración: `alembic revision --autogenerate -m "descripcion"`
> 2. Aplicar la migración localmente: `alembic upgrade head`
> 3. **Aplicar la migración en PRODUCCIÓN** después del despliegue: `docker exec masas_estacion_backend alembic upgrade head`
>
> Si olvidas esto, la aplicación fallará con errores como `UndefinedColumn` o `RelationUndefined`.
```bash
# Acceder a PostgreSQL
docker exec -it fme-postgres psql -U fme -d fme_database

# Crear migración con Alembic
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial de migraciones
alembic history
```

### Scripts de Carga de Datos

```bash
# Cargar productos desde CSV
docker exec fme-backend python scripts/load_productos.py

# Cargar locales
docker exec fme-backend python scripts/load_locales.py

# Inicializar inventario (100 unidades por producto/local)
docker exec fme-backend python scripts/load_inventario_inicial.py
```

## 🧪 Testing

```bash
pytest

# Con cobertura
pytest --cov=.

# Tests específicos
pytest tests/test_inventario.py
```

## 🔒 Variables de Entorno

Archivo `.env`:

```env
# PostgreSQL
DB_USER=fme
DB_PASSWORD=fme
DB_NAME=fme_database

# URL de conexión (usa 'db' como host en Docker)
DATABASE_URL=postgresql://fme:fme@db:5432/fme_database

# Para desarrollo local usar:
# DATABASE_URL=postgresql://fme:fme@localhost:5432/fme_database
```

## 🌐 CORS y Frontend

La API permite requests desde el frontend:

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Landing Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Estado del Proyecto

### ✅ Completado

- [x] Configuración Docker con PostgreSQL
- [x] 7 modelos de datos con relaciones
- [x] Sistema de migraciones Alembic
- [x] Carga inicial de datos (16 productos, 4 locales)
- [x] Endpoints de inventario y catálogo
- [x] Precios diferenciados por local
- [x] Local "WEB" para e-commerce
- [x] Documentación OpenAPI

### 🚧 En Desarrollo

- [ ] Endpoint de creación de pedidos
- [ ] Sistema de leads (captura de contactos)
- [ ] Autenticación y autorización
- [ ] Tests de integración completos

## 🐛 Troubleshooting

### Error "Can't connect to database"

1. Verificar que el contenedor PostgreSQL esté corriendo:
```bash
docker ps | grep fme-postgres
```

2. Revisar logs del backend:
```bash
docker logs fme-backend --tail 50
```

### Migraciones pendientes

```bash
# Ver estado actual
docker exec fme-backend alembic current

# Aplicar todas las migraciones
docker exec fme-backend alembic upgrade head
```

### Reiniciar base de datos

```bash
docker-compose down -v  # Elimina volúmenes
docker-compose up -d
# Volver a ejecutar scripts de carga
```

## 💾 Gestión de Datos en Producción (Best Practices)

Para actualizar datos de configuración (como Items de Menú, Roles, Parámetros) en producción, se recomienda encarecidamente:

1.  **NO usar SQL directo**: Esto evita inconsistencias de ids, bloqueos de tabla y errores humanos.
2.  **Usar Scripts Python via API**: Garantiza que se ejecuten las validaciones de negocio y permite operar remotamente sin túneles VPN.
3.  **Autenticación Segura**: Los scripts se autentican como Admin (`admin@fme.cl`).

### Scripts de Mantenimiento (`/scripts`)

*   `seed_produccion_menu.py`: Sincroniza el menú de producción creando opciones faltantes (ej: Compras, Producción).
*   `fix_icons_produccion.py`: Normaliza los iconos del menú usando Emojis para compatibilidad total.
*   `fix_menu_produccion.py`: Elimina asignaciones de menú obsoletas (ej: items antiguos eliminados).

**Ejemplo de Ejecución:**
```bash
# Desde local, apuntando a Producción
python scripts/seed_produccion_menu.py
```

## 📝 Licencia

[Especificar licencia]
