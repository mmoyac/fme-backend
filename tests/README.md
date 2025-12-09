# 🧪 Suite de Tests - FME Backend

## 📊 Resumen

**Estado:** ✅ **32/32 tests pasando** (100%)

Esta suite de tests cubre los endpoints críticos y la lógica de negocio del backend FME (FastAPI + SQLAlchemy + PostgreSQL).

## 🏗️ Estructura de Tests

```
tests/
├── conftest.py                  # Fixtures y configuración
├── test_productos.py            # CRUD de productos (7 tests)
├── test_inventario.py           # Gestión de inventario (5 tests)
├── test_pedidos.py              # Flujo de pedidos (5 tests)
├── test_movimientos.py          # Transferencias (4 tests)
├── test_dashboard.py            # Estadísticas (4 tests)
└── test_clientes.py             # CRUD de clientes (7 tests)
```

## ✅ Cobertura de Tests

### 1. **Productos** (`test_productos.py`) - 7 tests
- ✅ Crear producto
- ✅ SKU duplicado (validación)
- ✅ Listar productos
- ✅ Obtener producto por ID
- ✅ Actualizar producto
- ✅ Eliminar producto
- ✅ Producto no existe (404)

### 2. **Inventario** (`test_inventario.py`) - 5 tests
- ✅ Crear inventario
- ✅ Actualizar inventario
- ✅ Listar inventario completo
- ✅ Resumen de inventario (stock agregado)
- ✅ Detalle de inventario por SKU

### 3. **Pedidos** (`test_pedidos.py`) - 5 tests
- ✅ Crear pedido desde frontend
- ✅ Confirmar pedido descuenta inventario
- ✅ Cancelar pedido devuelve inventario
- ✅ Validación de stock insuficiente
- ✅ Listar pedidos

**Flujo de negocio validado:**
1. Crear pedido → Estado PENDIENTE (sin descuento)
2. Confirmar pedido → Estado CONFIRMADO (descuenta stock, crea movimiento)
3. Cancelar pedido → Estado CANCELADO (devuelve stock, crea movimiento de ajuste)

### 4. **Movimientos de Inventario** (`test_movimientos.py`) - 4 tests
- ✅ Transferir inventario entre locales
- ✅ Validación de stock insuficiente
- ✅ Listar historial de movimientos
- ✅ Filtrar movimientos por producto

**Tipos de movimientos:**
- `TRANSFERENCIA`: Movimiento manual entre locales
- `PEDIDO`: Descuento por confirmación de pedido
- `AJUSTE`: Devolución por cancelación

### 5. **Dashboard** (`test_dashboard.py`) - 4 tests
- ✅ Estadísticas generales (ventas, pedidos, clientes)
- ✅ Pedidos confirmados y estados
- ✅ Métrica de pedidos por cobrar
- ✅ Top productos más vendidos

**Métricas validadas:**
- Ventas del día/mes
- Total de pedidos por estado
- Pedidos por cobrar (no pagados)
- Ticket promedio
- Top 5 productos vendidos
- Stock bajo (< 10 unidades)
- Ventas por día (últimos 7 días)

### 6. **Clientes** (`test_clientes.py`) - 7 tests
- ✅ Crear cliente
- ✅ Email duplicado (validación)
- ✅ Listar clientes
- ✅ Obtener cliente por ID
- ✅ Actualizar cliente
- ✅ Eliminar cliente sin pedidos
- ✅ Protección: no eliminar cliente con pedidos

## 🛠️ Ejecutar Tests

### Dentro del contenedor Docker:
```bash
docker-compose exec backend pytest tests/ -v
```

### Con reporte detallado:
```bash
docker-compose exec backend pytest tests/ -v --tb=short
```

### Tests específicos:
```bash
# Un módulo
docker-compose exec backend pytest tests/test_pedidos.py -v

# Un test específico
docker-compose exec backend pytest tests/test_pedidos.py::test_crear_pedido -vv
```

### Con cobertura:
```bash
docker-compose exec backend pytest tests/ --cov=. --cov-report=html
```

## 📋 Fixtures Disponibles

### `db_session`
Sesión de base de datos SQLite en memoria (independiente por test).

### `client`
Cliente de prueba de FastAPI con base de datos de test. Automáticamente crea el local `WEB` requerido.

### `sample_producto`
Producto de ejemplo: "Pan Amasado" (SKU: PAN-001)

### `sample_local`
Local físico de ejemplo: "Sucursal Centro"

### `sample_cliente`
Cliente de ejemplo con email, teléfono y dirección

### `producto_con_inventario`
Producto completo con:
- Precio configurado en local físico
- Precio configurado en local WEB
- Stock inicial: 100 unidades

## 🔧 Configuración de Tests

### `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short --disable-warnings
```

### Base de datos
Los tests usan **SQLite en memoria** (`sqlite:///:memory:`) para:
- ✅ Velocidad (no I/O de disco)
- ✅ Aislamiento (cada test es independiente)
- ✅ No contamina la BD de producción

## 🚀 Integración Continua

### Preparación para CI/CD:
```yaml
# .github/workflows/tests.yml (ejemplo)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d db
          docker-compose run backend pytest tests/ -v
```

## 📈 Próximos Pasos

### Backend (Opcional):
- [ ] Tests de locales (CRUD)
- [ ] Tests de precios (CRUD)
- [ ] Tests de autenticación (si se implementa)
- [ ] Tests de carga (stress testing)
- [ ] Integración con coverage badge

### Frontend:
- [ ] Tests de componentes React (Jest + Testing Library)
- [ ] Tests de formularios (checkout, admin forms)
- [ ] Tests de estados globales

### E2E:
- [ ] Tests Playwright/Cypress
- [ ] Flujo cliente: navegar → agregar al carrito → checkout
- [ ] Flujo admin: login → crear producto → gestionar inventario → confirmar pedido

## 🐛 Debugging de Tests

### Ver logs detallados:
```bash
docker-compose exec backend pytest tests/ -vv -s --log-cli-level=INFO
```

### Detener en el primer fallo:
```bash
docker-compose exec backend pytest tests/ -x
```

### Ejecutar solo tests que fallaron:
```bash
docker-compose exec backend pytest tests/ --lf
```

## ✨ Buenas Prácticas Implementadas

1. **Fixtures reutilizables:** Datos de prueba centralizados en `conftest.py`
2. **Tests independientes:** Cada test tiene su propia base de datos limpia
3. **Validaciones completas:** No solo happy path, también casos de error
4. **Nombres descriptivos:** Los nombres de tests explican exactamente qué validan
5. **Base de datos de test:** Separada de producción usando SQLite in-memory
6. **Fixtures en cascada:** `producto_con_inventario` incluye precio y stock automáticamente

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

---

**Última actualización:** 2025-11-24  
**Estado:** ✅ Todos los tests pasando (32/32)
