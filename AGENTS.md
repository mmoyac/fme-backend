# 🤖 AGENTS.md: Backend FME - Guía Operacional (FastAPI, SQLAlchemy, PostgreSQL)

Este archivo sirve como el **manual de operaciones** y contexto esencial para cualquier agente de codificación o desarrollador que interactúe con el repositorio `https://github.com/mmoyac/fme-backend.git`.

El objetivo es mantener la consistencia en el entorno, el código y la arquitectura de la base de datos.

---

## 🏢 Arquitectura Multi-Tenant SaaS

**El sistema es multi-tenant con detección automática por dominio.**

### Estructura de Dominios (Producción)

```
Landing Pages (Por tenant):
├─ masasestacion.cl              → Masas Estación (tenant 1)
└─ elolivo.masasestacion.cl      → El Olivo (tenant 2)

Infraestructura (Única):
├─ api.masasestacion.cl          → API REST
└─ admin.masasestacion.cl        → Backoffice multi-tenant
```

### Detección Automática de Tenant

El sistema detecta el tenant basándose en el header `Host` de la petición HTTP:

```python
# services/tenant_service.py
def get_tenant_from_request(request: Request, db: Session):
    # 1. Match exacto por dominio_principal
    # 2. Localhost → tenant_id=1 (desarrollo)
    # 3. Subdominio (.masasestacion.cl) → buscar por subdomain
    # 4. Fallback → tenant_id=1
```

**Endpoints públicos con detección automática:**
- `GET /api/config/landing` - Configuración de landing page
- `GET /api/productos/catalogo` - Catálogo de productos

**NO** se requiere enviar `tenant_id` como query parameter.

---

## 1. ⚙️ Arquitectura del Proyecto y Convenciones

### 1.1. Stack Tecnológico

| Componente | Tecnología | Rol |
| :--- | :--- | :--- |
| **Framework** | FastAPI (Python) | Capa de API REST. |
| **ORM** | SQLAlchemy (Core + ORM) | Mapeo objeto-relacional. |
| **Base de Datos** | PostgreSQL (v14+) | Almacenamiento persistente. |
| **Orquestación** | Docker Compose | Entorno de desarrollo aislado. |
| **Tests** | pytest + httpx | Suite de tests automatizados. |

### 1.2. Estructura del Directorio

El código fuente del backend (`fme-backend`) utiliza una arquitectura modular. Los agentes deben adherirse a esta convención al crear nuevos archivos o características:

* `main.py`: Punto de entrada de la aplicación FastAPI.
* `routers/`: Contiene los *endpoints* de la API agrupados por dominio de negocio (e.g., `routers/pedidos.py`).
* `schemas/`: Modelos de datos de solicitud/respuesta (**Pydantic**).
* `database/`: Lógica de conexión a SQLAlchemy (`database.py`) y modelos de la base de datos (`models.py`).
* `services/`: Lógica de negocio (CRUDs complejos, procesamiento de datos).
* `migrations/`: Directorio autogenerado y gestionado por **Alembic**.
* `tests/`: Pruebas unitarias y de integración (**32 tests automatizados**).

### 1.3. Convenciones de Codificación

* **Estilo:** PEP 8 (gestionado por herramientas de *linting* como Black o Ruff).
* **Nomenclatura:** Clases y *routers* en PascalCase. Funciones y variables en snake_case.
* **Gestión de Dependencias:** Se usa **`pip`** y el entorno virtual (`.venv`). El archivo **`requirements.txt`** es la única fuente de verdad para dependencias.
* **Seguridad (CRÍTICO):** Todo nuevo endpoint de gestión (Backoffice) DEBE estar protegido con `Depends(get_current_active_user)` o, si es un router completo, agregarlo como dependencia global en `main.py`. Solo endpoints públicos explicítos (e.g. Landing Page) pueden quedar abiertos.

### 1.4. 🔴 ENTORNO VIRTUAL (OBLIGATORIO)

**⚠️ REGLA CRÍTICA:** Este proyecto **SIEMPRE** debe usar el entorno virtual de Python ubicado en `venv/`.

**NUNCA uses comandos Python globales** como `python`, `pip`, o `uvicorn` directamente. Esto causará errores de dependencias faltantes.

#### ✅ Comandos CORRECTOS (Usar SIEMPRE):

```bash
# Ejecutar el servidor de desarrollo
.\venv\Scripts\uvicorn.exe main:app --reload

# Ejecutar scripts Python
.\venv\Scripts\python.exe scripts/seed_api.py
.\venv\Scripts\python.exe scripts/seed_menu_rbac.py

# Instalar nuevas dependencias
.\venv\Scripts\python.exe -m pip install nombre-paquete

# Actualizar requirements.txt después de instalar
.\venv\Scripts\python.exe -m pip freeze > requirements.txt

# Ejecutar tests
.\venv\Scripts\pytest.exe tests/ -v

# Ejecutar migraciones de Alembic
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\alembic.exe revision --autogenerate -m "descripción"
```

#### ❌ Comandos INCORRECTOS (NO usar):

```bash
# ❌ NO usar Python global
python scripts/seed_api.py
uvicorn main:app --reload
pip install mercadopago
pytest tests/

# Estos comandos usarían el Python global y fallarían por dependencias faltantes
```

#### Crear el entorno virtual (solo primera vez):

```bash
# Crear entorno virtual
python -m venv venv

# Instalar todas las dependencias
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### Activar entorno (opcional, para trabajar en terminal):

```bash
# Windows PowerShell
.\venv\Scripts\activate

# Después de activar, puedes usar comandos sin el prefijo:
python scripts/seed_api.py
uvicorn main:app --reload
```

**Nota:** Aunque activar el entorno es opcional, se recomienda usar siempre las rutas completas (`.\venv\Scripts\python.exe`) para evitar confusiones y garantizar que se use el entorno correcto.

---

## 2. 🐳 Configuración del Entorno de Desarrollo

Se requiere **Docker** y **Docker Compose** para iniciar los dos servicios principales: **`db`** (PostgreSQL) y **`backend`** (FastAPI).

### 2.1. Variables de Entorno (`.env`)

El archivo **`.env`** en la raíz del proyecto es la fuente de configuración. El servicio **`backend`** lo utiliza para definir su conexión a la base de datos.

```bash
# Variables de PostgreSQL (Servicio 'db')
DB_USER=fme
DB_PASSWORD=fme
DB_NAME=fme_database

# La URL de conexión utiliza 'db' como host (el nombre del servicio Docker)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}

# Mercado Pago (Sandbox / Producción)
MP_ACCESS_TOKEN=TEST-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 2.2. Comandos Docker

```bash
# Iniciar servicios (backend + base de datos)
docker-compose up -d

# Ver logs del backend
docker-compose logs -f backend

# Reiniciar backend
docker-compose restart backend

# Detener todos los servicios
docker-compose down
```

### 2.3. Despliegue en Producción

**Docker Hub:**
- Imagen: `mmoyac/masas-estacion-backend:latest`
- Automatización: Migraciones se ejecutan automáticamente al iniciar contenedor

**Arquitectura de Producción:**
```
┌─────────────────────────────────────────┐
│  VPS: 168.231.96.205                    │
├─────────────────────────────────────────┤
│  Backend (Puerto 8001)                  │
│  - Healthcheck automático               │
│  - Migraciones auto-aplicadas           │
│  - entrypoint.sh ejecuta alembic        │
├─────────────────────────────────────────┤
│  PostgreSQL 14 (Puerto interno 5432)    │
│  - Healthcheck: pg_isready              │
│  - Volumen persistente                  │
└─────────────────────────────────────────┘
```

**Script de Entrypoint (`entrypoint.sh`):**
```bash
#!/bin/bash
set -e

# 1. Esperar PostgreSQL usando SQLAlchemy
# 2. Ejecutar: alembic upgrade head
# 3. Iniciar: uvicorn main:app
```

**Comandos de Producción:**
```bash
# Build y push a Docker Hub
docker build -t mmoyac/masas-estacion-backend:latest -f Dockerfile.prod .
docker push mmoyac/masas-estacion-backend:latest

# Desplegar en VPS
ssh root@168.231.96.205 "cd docker/masas-estacion && \
  docker compose -f docker-compose.prod.yml pull backend && \
  docker compose -f docker-compose.prod.yml up -d backend"

# Ver logs en producción
ssh root@168.231.96.205 "docker logs masas_estacion_backend --tail 50"
```

---

## 3. 🧪 Suite de Tests Automatizados

### 3.1. Estado Actual

**✅ 32/32 tests pasando (100%)**

El backend cuenta con una suite completa de tests automatizados que valida todos los flujos de negocio críticos.

### 3.2. Estructura de Tests

```
tests/
├── conftest.py              # Fixtures y configuración (SQLite in-memory)
├── test_productos.py        # CRUD de productos (7 tests)
├── test_inventario.py       # Gestión de inventario (5 tests)
├── test_pedidos.py          # Flujo completo de pedidos (5 tests)
├── test_movimientos.py      # Transferencias de inventario (4 tests)
├── test_dashboard.py        # Estadísticas y métricas (4 tests)
├── test_clientes.py         # CRUD de clientes (7 tests)
├── README.md                # Documentación completa de tests
└── pytest.ini               # Configuración de pytest
```

### 3.3. Ejecutar Tests

```bash
# Todos los tests
docker-compose exec backend pytest tests/ -v

# Con cobertura
docker-compose exec backend pytest tests/ --cov=. --cov-report=html

# Test específico
docker-compose exec backend pytest tests/test_pedidos.py::test_crear_pedido -vv

# Detener en primer fallo
docker-compose exec backend pytest tests/ -x

# Solo tests que fallaron previamente
docker-compose exec backend pytest tests/ --lf
```

### 3.4. Fixtures Disponibles

| Fixture | Descripción |
| :--- | :--- |
| `db_session` | Sesión de BD SQLite en memoria (aislada por test) |
| `client` | Cliente FastAPI con BD de test y local WEB creado |
| `sample_producto` | Producto "Pan Amasado" (SKU: PAN-001) |
| `sample_local` | Local físico "Sucursal Centro" |
| `sample_cliente` | Cliente con email, teléfono y dirección |
| `producto_con_inventario` | Producto con precio en WEB + local físico, stock: 100 |

### 3.5. Cobertura de Tests

#### Flujos de Negocio Validados:
- ✅ Crear pedido desde frontend → Estado PENDIENTE
- ✅ Confirmar pedido → Descuenta inventario, crea movimiento PEDIDO
- ✅ Cancelar pedido → Devuelve inventario, crea movimiento AJUSTE
- ✅ Transferir inventario → Valida stock, registra movimiento TRANSFERENCIA
- ✅ Dashboard → Calcula ventas, pedidos por estado, por cobrar, top productos
- ✅ Clientes → No permite eliminar si tiene pedidos asociados

#### Validaciones Críticas:
- ✅ SKU único en productos
- ✅ Email único en clientes
- ✅ Stock suficiente antes de confirmar pedido
- ✅ Stock suficiente antes de transferir
- ✅ No descontar inventario dos veces
- ✅ Protección de integridad referencial

### 3.6. Convenciones para Nuevos Tests

1. **Nombres descriptivos:** `test_<accion>_<resultado_esperado>`
2. **Arrange-Act-Assert:** Preparar datos → Ejecutar acción → Verificar resultado
3. **Fixtures reutilizables:** Usar fixtures de `conftest.py`
4. **Base de datos limpia:** Cada test usa su propia sesión aislada
5. **Validar errores:** Incluir tests para casos de error (400, 404, 422)

**Ver documentación completa:** `tests/README.md`

---

## 4. 🗄️ Base de Datos y Modelos

### 4.1. Tablas Principales

| Tabla | Descripción | Campos Clave |
| :--- | :--- | :--- |
| `productos` | Catálogo de productos | `id`, `nombre`, `sku`, `descripcion`, `imagen_url` |
| `locales` | Sucursales/Tienda Online | `id`, `codigo`, `nombre`, `direccion` |
| `clientes` | Clientes del sistema | `id`, `nombre`, `email`, `telefono`, `direccion` |
| `inventario` | Stock por producto/local | `producto_id`, `local_id`, `cantidad_stock` |
| `precios` | Precios por producto/local | `producto_id`, `local_id`, `monto_precio` |
| `pedidos` | Órdenes de compra | `id`, `cliente_id`, `local_id`, `estado`, `total`, `puntos_ganados`, `puntos_usados` |
| `items_pedido` | Detalle de pedidos | `pedido_id`, `producto_id`, `cantidad`, `precio_unitario` |
| `puntos_cliente` | Estado de puntos por cliente | `cliente_id`, `puntos_disponibles`, `puntos_totales_ganados` |
| `movimientos_puntos` | Historial de puntos | `id`, `cliente_id`, `pedido_id`, `tipo_movimiento`, `puntos` |
| `turnos_caja` | Turnos de trabajo en caja | `id`, `vendedor_id`, `local_id`, `fecha_apertura`, `estado`, `monto_inicial` |
| `operaciones_caja` | Operaciones financieras | `id`, `turno_caja_id`, `tipo_operacion`, `monto`, `descripcion` |
| `movimientos_inventario` | Historial de movimientos | `id`, `tipo_movimiento`, `cantidad`, `fecha` |

### 4.2. Relaciones Importantes

```
productos (1) ----< (N) inventario
productos (1) ----< (N) precios
productos (1) ----< (N) items_pedido

locales (1) ----< (N) inventario
locales (1) ----< (N) precios
locales (1) ----< (N) pedidos (local_id)
locales (1) ----< (N) pedidos (local_despacho_id)

clientes (1) ----< (N) pedidos
pedidos (1) ----< (N) items_pedido

despachos (1) ----< (N) picking_items
usuarios (1) ----< (N) despachos (despachador)
pedidos (1) ---< (1) despachos

movimientos_inventario >---- (1) productos
movimientos_inventario >---- (1) local_origen
movimientos_inventario >---- (1) local_destino
```

### 4.3. Tablas del Sistema de Despachos (NUEVO)

| Tabla | Descripción | Campos Clave |
| :--- | :--- | :--- |
| `despachos` | Gestión de entregas | `id`, `pedido_id`, `despachador_user_id`, `estado`, `fecha_creacion`, `fecha_entrega` |
| `picking_items` | Items para recolección | `id`, `despacho_id`, `producto_id`, `cantidad_solicitada`, `cantidad_recogida`, `completado` |

### 4.4. Estados del Sistema de Despachos

**EstadoDespacho (Enum):**
```
ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO
```

- **ASIGNADO**: Despacho asignado a despachador, pendiente de picking
- **EN_PICKING**: Proceso de recolección de productos activo
- **LISTO_EMPAQUE**: Todos los items recogidos, listo para empacar y enviar
- **EN_RUTA**: Despachador en camino al cliente
- **ENTREGADO**: Entrega completada exitosamente

### 4.5. Local WEB (Especial)

El local con `codigo = 'WEB'` es **virtual** y actúa como agregador de precios:
- **No tiene stock físico** (su stock es la suma de locales físicos)
- **Se usa para pedidos frontend** (definir precios visibles al público)
- **No se despacha desde aquí** (se elige local físico al confirmar)

---

---

## 5. 🔐 Autenticación y Usuarios

### 5.1. Usuarios y Roles
El sistema utiliza autenticación basada en JWT (JSON Web Tokens). Existen dos entidades principales:
*   **Roles:** Definen los privilegios (e.g., `admin`).
*   **Users:** Usuarios con acceso al sistema, asociados a un rol.

### 5.2. Usuario Administrador Inicial
Para entornos nuevos o de desarrollo, existe un endpoint de ayuda para crear el primer administrador.

**Crear Admin Inicial (Solo si no existen usuarios):**
`POST /api/auth/setup/create_admin`

Body sugerido:
```json
{
  "email": "admin@fme.cl",
  "password": "admin",
  "nombre_completo": "Super Admin",
  "role_id": 0
}
```

> ** Nota:** Este endpoint fallará si ya existe al menos un usuario en la base de datos.

### 5.3. Gestión de Usuarios (Backoffice)
Un usuario con rol `admin` puede gestionar otros usuarios mediante los endpoints:
*   `GET /api/admin/users`: Listar usuarios.
*   `POST /api/admin/users`: Crear nuevo usuario.
*   `POST /api/admin/roles`: Crear nuevos roles.

---

## 6. 🔄 Gestión de Migraciones con Alembic

### 5.1. Comandos de Migraciones

```bash
# Generar migración automática
docker-compose exec backend alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones pendientes (desarrollo)
docker-compose exec backend alembic upgrade head

# Ver historial de migraciones
docker-compose exec backend alembic history

# Revertir última migración
docker-compose exec backend alembic downgrade -1

# Ver estado actual en producción
ssh root@168.231.96.205 "docker exec masas_estacion_backend alembic current"
```

### 5.2. Migraciones Aplicadas

**Cadena de Migraciones:**
1. `921430423f7b` - Migración inicial (todas las tablas)
2. `042fe92e014b` - Campo `imagen_url` en productos
3. `9e72c2b2d9d3` - (vacía)
4. `78d3e9622bf7` - Campos `direccion` y `comuna` en clientes, `notas` en pedidos
5. `787f179b0bed` - Campo `local_despacho_id` e `inventario_descontado` en pedidos
6. `25d2067d81f2` - Tabla `movimientos_inventario` (HEAD)
7. `2933e69a77f2` - Campo `codigo` en locales

### 5.3. Migraciones Automáticas en Producción

**✅ Las migraciones se ejecutan automáticamente** al iniciar el contenedor mediante `entrypoint.sh`:

```bash
🔄 Esperando a que PostgreSQL esté listo...
✅ PostgreSQL está listo
🔄 Ejecutando migraciones de Alembic...
alembic upgrade head
✅ Migraciones aplicadas exitosamente
🚀 Iniciando servidor FastAPI...
```

**Beneficios:**
- No requiere intervención manual en producción
- Garantiza que la BD esté actualizada antes de iniciar la API
- Logs claros del proceso de migración

---

## 6. 📡 Endpoints de la API

### 6.1. Productos

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/productos/` | Listar todos los productos |
| `GET` | `/api/productos/{id}` | Obtener producto por ID |
| `POST` | `/api/productos/` | Crear producto |
| `PUT` | `/api/productos/{id}` | Actualizar producto |
| `DELETE` | `/api/productos/{id}` | Eliminar producto |

### 6.2. Inventario

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/inventario/` | Listar todo el inventario |
| `GET` | `/api/inventario/resumen` | Resumen con stock total por producto |
| `GET` | `/api/inventario/detalle/{sku}` | Detalle de stock por local |
| `PUT` | `/api/inventario/producto/{id}/local/{id}` | Actualizar stock |

### 6.3. Pedidos

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/pedidos/` | Crear pedido (desde landing) |
| `GET` | `/api/pedidos/` | Listar pedidos |
| `GET` | `/api/pedidos/{id}` | Obtener pedido con detalle |
| `PUT` | `/api/pedidos/{id}` | Actualizar estado/local de despacho |

### 6.4. Movimientos de Inventario

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/movimientos/transferencia` | Transferir stock entre locales |
| `GET` | `/api/movimientos/historial` | Historial de movimientos (filtrable) |

### 6.5. Dashboard

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard/estadisticas` | Todas las métricas (ventas, pedidos, top productos, etc.) |

### 6.6. Clientes

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/clientes/` | Listar clientes con información de puntos |
| `POST` | `/api/clientes/` | Crear cliente |
| `PUT` | `/api/clientes/{id}` | Actualizar cliente |
| `DELETE` | `/api/clientes/{id}` | Eliminar cliente (solo sin pedidos) |

### 6.7. Sistema de Puntos

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/clientes/{id}` | Información completa de puntos del cliente |
| `POST` | `/api/pedidos/` | Crear pedido con cálculo automático de puntos |
| `POST` | `/api/pedidos/backoffice` | Crear pedido con opción de canje de puntos |
| `PUT` | `/api/pedidos/{id}` | Otorgar/devolver puntos según cambio de estado |

### 6.8. Sistema de Caja

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/caja/estado` | Estado actual de caja del vendedor |
| `POST` | `/api/caja/turno/abrir` | Abrir nuevo turno de caja |
| `PUT` | `/api/caja/turno/{id}/cerrar` | Cerrar turno con conteo final |
| `POST` | `/api/caja/operacion` | Registrar operación financiera |
| `GET` | `/api/caja/turnos/historial` | Historial de turnos |
| `GET` | `/api/caja/turno/{id}` | Detalle completo del turno |
| `GET` | `/api/caja/turno/{id}/pdf` | Descargar PDF del cierre |

### 6.9. Sistema de Cajas Variables (NUEVO)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/stock-cajas/lotes-disponibles/{producto_id}` | Lotes FIFO disponibles para asignación |
| `GET` | `/api/stock-cajas/resumen` | Resumen de stock de cajas por proveedor |
| `POST` | `/api/pedidos/` | Crear pedido (detecta tipo automáticamente) |
| `PUT` | `/api/pedidos/{id}` | Confirmar/cancelar con lógica de lotes específicos |

### 6.10. Sistema de Despachos (NUEVO)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/despachos/asignar/{pedido_id}` | Asignar pedido confirmado a despachador |
| `GET` | `/api/despachos/` | Listar despachos con filtros por estado |
| `GET` | `/api/despachos/{id}` | Obtener despacho específico con detalles completos |
| `PUT` | `/api/despachos/{id}` | Actualizar estado, hora estimada y notas |
| `POST` | `/api/despachos/{id}/iniciar-picking` | Iniciar proceso de picking (ASIGNADO → EN_PICKING) |
| `PUT` | `/api/despachos/picking-item/{item_id}` | Actualizar cantidad recogida de item específico |
| `POST` | `/api/despachos/{id}/completar-picking` | Completar picking (EN_PICKING → LISTO_EMPAQUE) |
| `GET` | `/api/despachos/estadisticas` | Métricas de performance de despachos |
| `GET` | `/api/despachos/{id}/tracking` | Información de tracking para despachador/cliente |

### 6.11. Dashboard Mejorado

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard/estadisticas` | Métricas de ventas y pedidos |
| `GET` | `/api/dashboard/metricas-caja` | Estado de todas las cajas |

---

## 7. 🔐 Reglas de Negocio Críticas

### 7.1. Estados de Pedido

```
PENDIENTE → CONFIRMADO → EN_PREPARACION → ENTREGADO
    ↓
CANCELADO
```

- **PENDIENTE:** Creado, sin descuento de inventario
- **CONFIRMADO:** Inventario descontado, local asignado, movimiento PEDIDO creado
- **EN_PREPARACION:** En proceso de preparación
- **ENTREGADO:** Completado exitosamente
- **CANCELADO:** Cancelado, inventario devuelto, movimiento AJUSTE creado

### 7.2. Descuento de Inventario

1. Al **crear pedido** → Estado PENDIENTE (NO descuenta)
2. Al **confirmar** → Valida stock, descuenta, marca `inventario_descontado = True`
3. Al **cancelar** → Si estaba descontado, devuelve stock, marca `inventario_descontado = False`

**Protección:** No se puede descontar dos veces (flag `inventario_descontado`).

### 7.3. Tipos de Movimientos

| Tipo | Descripción | Se crea automáticamente |
| :--- | :--- | :--- |
| `TRANSFERENCIA` | Movimiento manual entre locales | Al hacer transferencia |
| `PEDIDO` | Descuento por confirmación | Al confirmar pedido |
| `AJUSTE` | Devolución por cancelación | Al cancelar pedido confirmado |
| `ENTRADA_INICIAL` | Carga inicial de stock | Manualmente |

### 7.4. Sistema de Caja (NUEVO)

**Estados de Turno:**
```
ABIERTO ← (apertura con monto inicial)
  ↓
CERRADO ← (cierre con conteo real y diferencia)
```

**Restricciones:**
- Un vendedor solo puede tener **un turno abierto** a la vez
- Solo puede abrir caja en su **local asignado** (`local_defecto_id`)
- Las operaciones se registran automáticamente al confirmar pedidos
- El cierre calcula automáticamente diferencias de efectivo

**Tipos de Operaciones:**
- `APERTURA`: Monto inicial del turno
- `VENTA`: Registro automático de ventas
- `INGRESO`: Dinero adicional que entra
- `EGRESO`: Dinero que sale (gastos, vueltos)
- `DEVOLUCION`: Devoluciones a clientes
- `CIERRE`: Operación final del turno

### 7.5. Sistema de Cajas Variables (NUEVO)

**Tipos de Pedido:**
- **PRODUCTOS (ID=1):** Inventario tradicional por unidades
- **CAJAS_VARIABLES (ID=2):** Inventario por lotes específicos con peso y precio/kg

**Flujo de Cajas Variables:**
```
Pedido PENDIENTE (precio estimado)
↓
Confirmar → Asignar lotes FIFO → Calcular precio real → Actualizar monto_total
↓
Lotes: disponible_venta=False, vendido=True
Stock: cajas_disponibles -= cantidad, cajas_totales_vendidas += cantidad
```

**Restauración al Cancelar:**
```
Cancelar pedido confirmado
↓
Lotes: disponible_venta=True, vendido=False
Stock: cajas_disponibles += cantidad, cajas_totales_vendidas -= cantidad (si > 0)
```

**FIFO (First In, First Out):**
- Lotes se asignan por `fecha_vencimiento ASC`
- Automatiza rotación de inventario perecedero
- Minimiza pérdidas por vencimiento

**Trazabilidad:**
- `MovimientoStockCajas` registra cada operación
- Tipos: `VENTA_LOTE`, `DEVOLUCION_LOTE`
- Campos: `lote_codigo`, `referencia_tipo`, `referencia_id`

### 7.7. Sistema de Despachos (NUEVO)

**Estados del Flujo:**
```
ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO
```

**Proceso Completo:**
1. **Asignar Despacho**: Pedido CONFIRMADO → Crear despacho ASIGNADO con despachador
2. **Iniciar Picking**: ASIGNADO → EN_PICKING, crear picking_items por cada producto del pedido
3. **Recolección**: Actualizar cantidad_recogida por cada item
4. **Completar Picking**: Todos items completos → EN_PICKING → LISTO_EMPAQUE
5. **En Ruta**: LISTO_EMPAQUE → EN_RUTA (manual desde backoffice)
6. **Entregar**: EN_RUTA → ENTREGADO con timestamp de entrega

**Automatizaciones:**
- Crear picking_items automáticamente al asignar despacho
- Validar que todos los items estén completos antes de finalizar picking
- Calcular tiempos de picking y eficiencia de entrega
- Tracking completo con timestamps por cada estado

### 7.8. Validaciones Importantes

- **SKU único:** No puede haber dos productos con el mismo SKU
- **Email único:** No puede haber dos clientes con el mismo email
- **Stock suficiente:** Antes de confirmar pedido o transferir
- **Lotes suficientes:** Validación específica para cajas variables
- **Consistencia lotes-stock:** Stock agregado debe coincidir con lotes reales
- **Protección de referencias:** No eliminar cliente con pedidos asociados
- **Local WEB requerido:** Debe existir para crear pedidos desde landing

---

## 8. 📝 Comandos Frecuentes

### 8.1. Docker

```bash
# Ver logs del backend
docker-compose logs -f backend

# Reiniciar backend
docker-compose restart backend

# Acceder a shell del contenedor
docker-compose exec backend bash

# Ver estado de contenedores
docker-compose ps
```

### 8.2. Tests

```bash
# Ejecutar tests
docker-compose exec backend pytest tests/ -v

# Tests con cobertura
docker-compose exec backend pytest tests/ --cov=. --cov-report=html

# Test específico
docker-compose exec backend pytest tests/test_pedidos.py -v
```

### 8.3. Base de Datos

```bash
# Aplicar migraciones
docker-compose exec backend alembic upgrade head

# Crear migración
docker-compose exec backend alembic revision --autogenerate -m "descripción"

# Acceder a PostgreSQL
docker-compose exec db psql -U fme -d fme_database
```

---

## 9. 📊 Estado Actual del MVP

### 9.1. Backend (100% Completado ✅)

**Funcionalidades Implementadas:**
- ✅ CRUD completo de Productos, Locales, Clientes
- ✅ Gestión de Inventario con stock por local
- ✅ Gestión de Precios por local
- ✅ Sistema completo de Pedidos (5 estados)
- ✅ Sistema completo de Puntos de Fidelización
- ✅ **Sistema completo de Caja y Turnos**
- ✅ **Control de flujo de efectivo por vendedor**
- ✅ **Restricciones de usuario por local asignado**
- ✅ **Generación de PDFs para cierre de caja**
- ✅ **Sistema de Cajas Variables con Lotes Específicos** (NUEVO)
- ✅ **Asignación Automática FIFO de Lotes por Peso y Precio** (NUEVO)
- ✅ **Actualización Automática de Precios: Estimado → Real** (NUEVO)
- ✅ **Inventario Dual: Productos Regulares vs Cajas Variables** (NUEVO)
- ✅ **Restauración Completa de Lotes al Cancelar Pedidos** (NUEVO)
- ✅ **Sistema Completo de Despachos (Delivery/Picking)** (NUEVO)
- ✅ **Estados de Despacho: ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO** (NUEVO)
- ✅ **Picking Items con Cantidades Solicitadas vs Recogidas** (NUEVO)
- ✅ **Tracking Completo de Tiempos por Estado** (NUEVO)
- ✅ **Estadísticas y Dashboard de Despachos** (NUEVO)
- ✅ Transferencias de inventario con historial
- ✅ Dashboard con métricas analíticas y de caja
- ✅ Timezone configurado (America/Santiago)
- ✅ 32+ tests automatizados (100% pasando)

**Características Técnicas:**
- FastAPI con Pydantic v2
- SQLAlchemy ORM + Alembic migrations
- PostgreSQL 14
- Docker + Docker Compose
- Suite de tests con pytest
- Base de datos de test (SQLite in-memory)

**Despliegue:**
- VPS: 168.231.96.205:8001
- Docker Hub: mmoyac/masas-estacion-backend:latest
- Estado: ✅ Operativo en producción
- Migraciones: ✅ Automáticas (via entrypoint.sh)

**Configuración de Producción:**
```yaml
# docker-compose.prod.yml
backend:
  image: mmoyac/masas-estacion-backend:latest
  container_name: masas_estacion_backend
  restart: always
  ports:
    - "8001:8000"
  environment:
    DATABASE_URL: postgresql://fme:fme@db:5432/fme_database
  healthcheck:
    test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/docs')"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### 9.2. Próximos Pasos Recomendados

**Backend (Opcional):**
- [ ] Tests de locales (CRUD)
- [ ] Tests de precios (CRUD)
- [x] Sistema de autenticación (JWT) ✅
- [x] Sistema de Puntos de Fidelización ✅
- [ ] Caché con Redis
- [ ] Rate limiting
- [x] Implementar Roles en todos los Endpoints ✅

**Integración:**
- [x] CI/CD con GitHub Actions ✅ (Despliegue automático a VPS)
- [ ] Cobertura de código badge
- [ ] Documentación automática (OpenAPI)

---

---

## 10. 🍽️ Sistema de Recetas y Producción

### 10.1. Conceptos Clave

El sistema conecta tres módulos: **Recetas** (qué ingredientes usa un producto), **Producción** (órdenes de fabricación) e **Inventario** (stock en kg/unidades decimales).

### 10.2. Modelo de Datos

```
Producto (producto fabricado)
 └─ Receta
     ├─ rendimiento: Decimal   → cuántas unidades produce la receta
     ├─ unidad_rendimiento_id  → unidad del rendimiento (ej: "unidad")
     └─ IngredienteReceta[]
         ├─ producto_ingrediente_id  → FK a Producto (materia prima)
         ├─ cantidad: Numeric(10,3)  → cantidad en unidad de inventario del ingrediente
         └─ unidad_medida_id        → unidad del ingrediente en la receta
```

### 10.3. Unidad de Compra vs Unidad de Inventario

Las materias primas a granel (harina, almendras, aceite, etc.) se compran en una unidad (sacos, cajas, bidones) pero el inventario se gestiona en la **unidad base** (kg, litros, gramos).

Campos en `Producto`:
- `unidad_medida_id` → unidad de inventario (ej: kg)
- `unidad_compra_descripcion` → texto libre (ej: "Saco 25 kg")
- `factor_conversion_compra` → cuántas unidades de inventario contiene 1 unidad de compra (ej: 25)

**Ejemplo:** Harina bio bio roja 25 kg
- `unidad_medida` = kg
- `unidad_compra_descripcion` = "Saco 25 kg"
- `factor_conversion_compra` = 25

Cuando se registra una compra de 1 saco → el sistema suma **25 kg** al inventario automáticamente.

### 10.4. Cálculo de Costos en Receta

El `precio_compra` del producto siempre se almacena en la **unidad de inventario** (ej: precio por kg).

Al recibir una compra:
```python
# routers/compras.py
factor = float(producto.factor_conversion_compra) or 1.0
# Stock: se suman cantidad × factor unidades
inventario.cantidad_stock += float(det.cantidad) * factor
# Precio: se divide por factor para obtener precio por unidad de inventario
producto.precio_compra = float(det.precio_unitario) / factor
```

**Ejemplo:** Compra 1 saco a $14.500
- Stock: +25 kg
- precio_compra: $14.500 / 25 = **$580/kg**

El costo de un ingrediente en la receta se calcula:
```
costo_total = cantidad_ingrediente_kg × precio_compra_por_kg
```
Ej: 0.044 kg × $580 = **$25,52**

### 10.5. Flujo de Producción

1. Se crea una `OrdenProduccion` con los productos a fabricar y cantidades
2. El sistema **valida stock** de todos los ingredientes antes de guardar:
   ```
   consumo_ingrediente = cantidad_ingrediente × (lote_a_producir / rendimiento_receta)
   ```
3. Al **finalizar** la orden, el sistema:
   - **Descuenta** del inventario de cada ingrediente (en kg/unidad base)
   - **Suma** al inventario del producto terminado (en su unidad)

**Ejemplo:** Producir 10 sopaipillas (rendimiento receta = 1 unidad)
- Harina requerida: 0.044 kg × (10 / 1) = **0.44 kg descontados**
- Sopaipillas: +10 unidades al stock

### 10.6. Inventario Decimal

El inventario soporta cantidades decimales (`Numeric(10,3)`) en todos los campos relevantes:

| Tabla | Campo | Tipo |
|-------|-------|------|
| `inventario` | `cantidad_stock` | Numeric(10,3) |
| `movimientos_inventario` | `cantidad` | Numeric(10,3) |
| `productos` | `stock_minimo`, `stock_critico` | Numeric(10,3) |
| `items_solicitud_transferencia` | `cantidad_*` | Numeric(10,3) |
| `picking_items` | `cantidad_*` | Numeric(10,3) |

> ⚠️ Los schemas Pydantic usan `float` (no `Decimal`) para estos campos, para que el JSON serialice como número y no como string.

### 10.7. Endpoints de Recetas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/recetas/productos/{id}/receta` | Obtener receta de un producto |
| POST | `/api/recetas/productos/{id}/receta` | Crear receta |
| DELETE | `/api/recetas/recetas/{id}` | Eliminar receta |
| POST | `/api/recetas/recetas/{id}/recalcular` | Recalcular costos |
| POST | `/api/recetas/recetas/{id}/ingredientes` | Agregar ingrediente |
| DELETE | `/api/recetas/ingredientes/{id}` | Eliminar ingrediente |

### 10.8. Endpoints de Producción

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/produccion/chequear-insumos/{producto_id}` | Verificar stock antes de producir |
| POST | `/api/produccion/ordenes` | Crear orden (valida stock) |
| GET | `/api/produccion/ordenes` | Listar órdenes |
| GET | `/api/produccion/ordenes/{id}` | Detalle de orden |
| POST | `/api/produccion/ordenes/{id}/finalizar` | Finalizar y actualizar inventario |

### 10.9. Reglas de Negocio Críticas

- Un producto con `tiene_receta = True` debe tener exactamente una receta activa para poder producirse.
- El stock de ingredientes se verifica **antes** de crear la orden; si falta stock, se rechaza con HTTP 400.
- El `precio_compra` del ingrediente se actualiza automáticamente cada vez que se recibe una compra.
- La receta almacena cantidades en la **unidad de inventario** del ingrediente (kg, no sacos).
- El backoffice muestra el stock en kg y la equivalencia en unidades de compra cuando el producto tiene `unidad_compra_descripcion` configurado.

---

**Última Actualización:** 2026-01-07
**Cambios Recientes:**
- ✅ **Sistema Completo de Despachos implementado** (NUEVO)
- ✅ **Modelos: Despacho, PickingItem con EstadoDespacho enum**
- ✅ **Schemas completos para todas las operaciones de despacho**
- ✅ **Router con 9 endpoints para flujo completo de delivery/picking**
- ✅ **Asignación automática de despachos a despachadores**
- ✅ **Sistema de picking con tracking de items individuales**
- ✅ **Estados: ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO**
- ✅ **Dashboard de métricas de despacho con estadísticas completas**
- ✅ **Tracking de tiempos por estado para optimización de procesos**
- ✅ **Integración con sistema de pedidos existente**
- ✅ Sistema completo de Cajas Variables implementado
- ✅ TipoPedido escalable: PRODUCTOS vs CAJAS_VARIABLES
- ✅ Asignación automática FIFO de lotes específicos
- ✅ Actualización automática de precios: estimado → real
- ✅ Inventario dual sincronizado: lotes individuales ↔ stock agregado
- ✅ Restauración completa al cancelar pedidos
- ✅ Endpoint `/api/stock-cajas/lotes-disponibles` con información detallada
- ✅ Trazabilidad completa con MovimientoStockCajas
- ✅ Modal de confirmación con detalles de lotes en frontend
- ✅ **Validación de consistencia entre lotes reales y stock registrado**
- ✅ Sistema completo de Puntos de Fidelización implementado
- ✅ PuntosService con cálculo por categoría de productos
- ✅ Endpoints de clientes enriquecidos con información de puntos
- ✅ Creación y confirmación de pedidos con otorgamiento automático de puntos
- ✅ Cancelación de pedidos con devolución automática de puntos
- ✅ Boletas PDF con información completa de puntos
- ✅ Endpoints de productos con información de categoría y puntos
- ✅ Workflow de CI/CD implementado (`docker-publish.yml`) para despliegue automático en VPS.
- ✅ Autenticación JWT y RBAC 100% funcional.
- ✅ Endpoint de Setup de Admin simplificado y protegido.
- ✅ Hash de contraseñas con Argon2.
- ✅ Despliegue en Docker Hub (mmoyac/masas-estacion-backend:latest).
- ✅ Configuración de producción optimizada.

**Repositorio:** `https://github.com/mmoyac/fme-backend.git`
**Docker Hub:** `https://hub.docker.com/r/mmoyac/masas-estacion-backend`
**API Producción:** `https://api.masasestacion.cl/docs`

---

## Módulo: Notas de Crédito y Devoluciones (implementado 2026-03-25)

### Conceptos clave

**Nota de crédito** es un documento tributario que anula total o parcialmente una boleta o factura. Se genera automáticamente en dos situaciones:
1. Al **cancelar** un pedido con documento tributario asociado.
2. Al **aprobar una devolución** parcial o total de un pedido entregado.

**Devolución** es el flujo formal para registrar que el cliente devolvió productos. Es independiente del cancelado. Un pedido en estado `ENTREGADO` solo puede cancelarse si ya tiene una devolución en estado `APROBADA`.

### Modelos de base de datos

```python
# database/models.py

class NotaCredito(Base):
    __tablename__ = "notas_credito"
    id, tenant_id, pedido_id (FK, no unique → one-to-many),
    tipo_documento_id (FK → NOTA_CREDITO_BOLETA o NOTA_CREDITO_FACTURA),
    monto, folio_sii, estado_sii, motivo, fecha_emision

class Devolucion(Base):
    __tablename__ = "devoluciones"
    id, tenant_id, pedido_id, nota_credito_id (FK nullable),
    usuario_id, motivo, fecha_devolucion, estado (PENDIENTE/APROBADA/RECHAZADA)
    items = relationship("ItemDevolucion", cascade="all, delete-orphan")

class ItemDevolucion(Base):
    __tablename__ = "items_devolucion"
    id, devolucion_id, item_pedido_id, producto_id,
    cantidad_devuelta, local_destino_id
```

La relación en `Pedido` es:
```python
notas_credito = relationship("NotaCredito", back_populates="pedido")  # lista, no uselist=False
devoluciones = relationship("Devolucion", back_populates="pedido")
```

### Servicios

**`services/notas_credito_service.py`**
```python
MAPA_NOTA_CREDITO = {"BOL": "NOTA_CREDITO_BOLETA", "FAC": "NOTA_CREDITO_FACTURA"}

class NotasCreditoService:
    def crear_si_corresponde(pedido, db):
        # Calcula ya_acreditado = sum(nc.monto for nc in pedido.notas_credito)
        # Solo crea NC por el monto pendiente (soporta NCs parciales previas)
        # estado_sii = "ANULADO" si pedido no tiene folio_sii
        # estado_sii = "PENDIENTE" si pedido ya tiene folio_sii registrado
```

**`services/devoluciones_service.py`**
- Crea la devolución y sus items
- Restaura stock por item en `local_destino_id`
- Llama a `NotasCreditoService.crear_si_corresponde()` para NC parcial
- Importa `MAPA_NOTA_CREDITO` desde `notas_credito_service` (fuente única)

### Reglas de negocio críticas

| Situación | Comportamiento |
|---|---|
| Cancelar pedido PENDIENTE/EN_PREPARACION | Genera NC si tiene doc. tributario. Devuelve stock si `inventario_descontado=True`. |
| Cancelar pedido ENTREGADO | **Bloqueado** hasta tener una devolución `APROBADA`. |
| Devolución parcial | Restaura solo las unidades devueltas. Genera NC por el monto proporcional. |
| Devolución total → luego cancelar | La NC de cancelación calcula `ya_acreditado` y crea NC solo por diferencia. |
| Factura sin folio SII | NC con `estado_sii = "ANULADO"` |
| Factura con folio SII ya registrado | NC con `estado_sii = "PENDIENTE"` (requiere envío manual al SII) |

### Restauración de stock en cancelación

```python
# routers/pedidos.py → _devolver_inventario_productos()
# Calcula ya_devuelto por devoluciones APROBADAS previas
# Solo restaura cantidad_pendiente = cantidad_original - ya_devuelto
# Evita doble restauración cuando hay devolución previa + cancelación
```

### Canales de venta

La tabla `canales_venta` tiene dos atributos que controlan el comportamiento del sistema:

| Campo | Tipo | Descripción |
|---|---|---|
| `entrega_inmediata` | bool | Si True, el pedido pasa automáticamente a ENTREGADO al crearse. Reemplaza el hardcode anterior basado en `local.codigo != 'WEB'`. |
| `visible_en_pos` | bool | Si False, el canal no aparece en el selector del POS. |

Valores por defecto:
- `POS`: `entrega_inmediata=True`, `visible_en_pos=True`
- `LANDING`: `entrega_inmediata=False`, `visible_en_pos=False`
- `WHATSAPP`, `TELEFONO`: `entrega_inmediata=False`, `visible_en_pos=True`

### Dashboard y Cobranza — montos netos

Todos los montos en dashboard y cobranza descuentan las notas de crédito emitidas:

```python
# routers/dashboard.py
nc_sq = db.query(
    NotaCredito.pedido_id,
    func.coalesce(func.sum(NotaCredito.monto), 0).label('total_nc')
).group_by(NotaCredito.pedido_id).subquery()

def monto_neto():
    return Pedido.monto_total - func.coalesce(nc_sq.c.total_nc, 0)
```

El endpoint `GET /api/pedidos/` incluye el campo `total_notas_credito` en cada pedido para que el frontend pueda calcular montos netos sin consultas adicionales.

### Casos de prueba validados (2026-03-25)

Todos los siguientes casos fueron probados en entorno de desarrollo con datos reales:

1. Devolución múltiples items distintos en un mismo pedido
2. Devolución a local distinto al de origen (stock se restaura en destino)
3. Pedido con cheque + devolución → NC correcta
4. Intento de devolución sobre pedido ya cancelado → bloqueado
5. Doble cancelación del mismo pedido → bloqueado
6. Devolución total con boleta → NC por monto completo con `estado_sii=ANULADO`
7. Cancelar en estado PENDIENTE con factura → NC generada, stock sin cambio (no se había descontado)
8. Devolución total con factura → NC por monto completo
9. Venta con stock exacto → sistema lo permite y deja stock en 0
10. Venta con stock insuficiente → bloqueado en UI (botón `+` limitado al stock disponible)
11. NC cuando factura ya tiene folio SII → `estado_sii = "PENDIENTE"` (no ANULADO)
**Estado MVP:** ✅ **Desplegado y operativo en producción**

## Módulo: Delivery — Configuración por Tenant (implementado 2026-03-25)

### Modelo de datos

Tabla `configuracion_landing` — campos de delivery:

| Columna | Tipo | Descripción |
|---|---|---|
| `costo_fijo_delivery` | `Numeric(10,2)` | Costo base fijo por pedido con delivery (CLP) |
| `costo_por_km_delivery` | `Numeric(10,2)` | Costo adicional por kilómetro (CLP) |
| `monto_minimo_delivery_gratis` | `Numeric(10,2)` | Si el pedido supera este monto, el delivery es gratuito. `NULL` = nunca gratis |
| `max_km_delivery` | `Numeric(6,2)` | Distancia máxima en km para aceptar pedidos con delivery. `NULL` = sin límite |

### Endpoint `/api/config/landing`

Incluye estos valores bajo la clave `delivery` en la respuesta JSON:

```python
"delivery": {
    "costo_fijo":        float(config.costo_fijo_delivery)         or None,
    "costo_por_km":      float(config.costo_por_km_delivery)        or None,
    "monto_minimo_gratis": float(config.monto_minimo_delivery_gratis) or None,
    "max_km":            float(config.max_km_delivery)              or None,
}
```

### Schemas Pydantic

`ConfiguracionLandingBase` y `ConfiguracionLandingUpdate` en `schemas/configuracion_landing.py`:

```python
max_km_delivery: Optional[float] = Field(None, ge=0,
    description="Distancia máxima en kilómetros para aceptar pedidos con delivery")
```

### Reglas de negocio

- El campo `costo_delivery` en la tabla `pedidos` almacena el costo acordado con el cliente. **No se suma al `monto_total`** — es informativo y se cobra aparte.
- La validación de `max_km` se realiza en el frontend (POS `EtapaFinalizacion`). El backend no rechaza pedidos por distancia; la restricción es UI.
- Si `max_km_delivery = NULL`, no hay límite de distancia.

### Migración

`d1e2f3a4b5c6_add_max_km_delivery_to_configuracion_landing.py` — agrega columna `max_km_delivery` a `configuracion_landing`.
