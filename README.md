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
| `pedidos` | Órdenes de compra | id, cliente_id, fecha_pedido, estado |
| `items_pedido` | Detalle de pedidos | pedido_id, producto_id, cantidad, precio_unitario |

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
- Response: `List[ProductoCatalogo]`

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

## 📝 Licencia

[Especificar licencia]
