## Context

El cliente usa la receta como una **planilla de costeo**: la `cantidad` de cada
ingrediente es un FACTOR (multiplicador) y los "ingredientes" incluyen ítems
operacionales (arriendo, electricidad, HH producción, desgaste maquinaria). El sistema
ya calcula `costo = (precio_compra / factor_conversion_compra) × cantidad` para todos
por igual, lo que es correcto para el costo. Los problemas están en tres capas:

1. `ingredientes_receta.cantidad` es `Numeric(10,3)` → trunca los factores a 3 decimales
   y el costo no calza con el Excel del cliente (que usa 4–8 decimales).
2. `main.py` → `DynamicCORSMiddleware` (sobre `BaseHTTPMiddleware`) solo agrega cabeceras
   CORS **después** de `await call_next(request)`. Si el handler lanza, `call_next`
   re-lanza y Starlette responde un `500` sin cabeceras CORS → "Failed to fetch".
3. `routers/recetas.py` → `calcular_costos_receta` asigna `Decimal` de alta precisión
   directo a `Numeric(10,2)` (riesgo de overflow) y los endpoints hacen múltiples
   `commit()` sin atomicidad. `routers/produccion.py` valida/descuenta stock de **todos**
   los ingredientes, incluidos los operacionales (pediría "stock de arriendo").

Constraint: fix de producción; minimizar regresiones, sobre todo en el middleware CORS
(transversal) y en el flujo de producción.

## Goals / Non-Goals

**Goals:**
- Preservar la precisión de los factores (`cantidad` con 8 decimales).
- Distinguir insumos físicos vs. operacionales para que producción no descuente stock
  de operacionales, manteniendo su aporte al costo.
- Errores visibles en el frontend (CORS en respuestas de error).
- Costos acotados (sin overflow) y persistencia atómica.

**Non-Goals:**
- Rediseñar el modelo de costos o el versionado de recetas.
- Cambiar la precisión de las columnas de costo (se mantienen `Numeric(10,2)`; el dinero
  va en pesos con 2 decimales).
- Rehacer el frontend (solo ajuste menor para ingresar/mostrar más decimales).

## Decisions

### 1. `cantidad` → `Numeric(18,8)` (migración Alembic)

Ampliar `ingredientes_receta.cantidad` a `Numeric(18,8)`: 8 decimales y 10 dígitos
enteros. Cubre todos los factores observados en el Excel con margen y elimina el
truncado. Esto **reemplaza** la idea previa de redondear `cantidad` a 3 decimales, que
habría destruido la precisión que el cliente necesita.

- **Alternativa (descartada)**: redondear a 3 decimales. Pierde precisión del factor.
- **Alternativa (anotada)**: 4 o 6 decimales. Suficiente para la columna FACTOR, pero
  sin margen para derivados de más precisión; se elige 8 para no volver a migrar.

### 2. Insumos operacionales: `TipoProducto.afecta_inventario`

Ya existe un mantenedor CRUD de Tipos de Producto en el backoffice (con tipos como
`MATERIA_PRIMA`, `MP`, `PRODUCTO_ELABORADO`, `PT`, `SP`, `INSUMO`, `SERVICIO`). Nos
colgamos de ahí: agregar `afecta_inventario` (bool, default `true`) a `TipoProducto` y
exponerlo como casilla en ese mantenedor. **No se seedea un tipo nuevo**: el cliente
clasifica sus ítems operacionales bajo el tipo `SERVICIO` existente (o el que prefiera)
y lo marca como que no afecta inventario. En `routers/produccion.py`, los loops de
validación y descuento de stock **omiten** los ingredientes cuyo `producto.tipo_producto`
tiene `afecta_inventario = false`. El cálculo de costos de la receta los sigue incluyendo.

- **Alternativa (descartada)**: decidir por código de tipo (`SERVICIO` → no stock).
  Frágil: la taxonomía está duplicada/suelta (`MP` vs `MATERIA_PRIMA`, `PT` vs
  `PRODUCTO_ELABORADO`); el flag declarativo es robusto y editable por el admin.
- **Alternativa (descartada)**: boolean por producto (`Producto.afecta_inventario`).
  Más granular pero redundante: el comportamiento depende del tipo, no del producto
  individual; el flag por tipo centraliza la regla y reusa el mantenedor existente.

### 3. CORS en errores: envolver `call_next` en try/except

En `DynamicCORSMiddleware.dispatch`, envolver `await call_next(request)` en `try/except`;
ante excepción, loggear el traceback y devolver una `JSONResponse(500)` con las cabeceras
CORS aplicadas si el origen es permitido.

- **Alternativa (descartada)**: `CORSMiddleware` estándar de Starlette — no soporta la
  validación dinámica de orígenes contra BD que el proyecto necesita.

### 4. Costos acotados + atomicidad

`calcular_costos_receta` aplica `quantize(Decimal("0.01"))` antes de asignar a columnas de
costo, deja de hacer `commit()` propio (solo muta objetos en la sesión), y el endpoint
hace **un único `commit()`** con `try/except` + `db.rollback()`. Validar que la parte
entera de cada costo cabe en `Numeric(10,2)`; si no, `HTTPException(422)` con mensaje claro.

## Risks / Trade-offs

- [Cambio en middleware CORS afecta toda la API] → Probar respuesta exitosa, preflight
  `OPTIONS`, error `500` y origen no permitido.
- [Omitir stock de operacionales cambia el flujo de producción] → Probar OT con insumos
  mixtos (físicos + operacionales) y confirmar que solo se descuentan los físicos.
- [Quitar `commit()` de `calcular_costos_receta` puede romper otros llamadores] →
  Revisar todos los usos (endpoint recalcular y handlers) y mover el commit al endpoint.
- [Migrar `cantidad` a 18,8 sobre datos existentes] → Es un `ALTER COLUMN TYPE` que
  preserva valores (solo amplía); validar en staging antes de prod.

## Migration Plan

1. Migración Alembic A: `ALTER COLUMN ingredientes_receta.cantidad TYPE Numeric(18,8)`.
2. Migración Alembic B: agregar `tipos_producto.afecta_inventario` (bool, default `true`).
   Aditiva, sin seed de tipos ni `UPDATE` de datos del tenant.
3. Desplegar backend (API del mantenedor expone/edita el flag) y backoffice (casilla).
4. El cliente marca el/los tipos operacionales (p. ej. `SERVICIO`) como
   `afecta_inventario = false` y clasifica sus productos operacionales bajo ese tipo,
   todo desde el backoffice.
5. Rollback: revertir migraciones (B es aditiva; A puede volver a `Numeric(10,3)` con
   posible pérdida de decimales nuevos) y el commit de código.

## Open Questions

- ¿Conviene que la migración B ponga `afecta_inventario = false` por defecto a `SERVICIO`
  (candidato obvio) para ahorrarle el paso al cliente, o dejamos todo en `true` y que el
  cliente lo configure? (Decisión menor; default seguro = `true` para todos.)
