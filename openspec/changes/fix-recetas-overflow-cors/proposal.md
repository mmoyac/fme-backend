## Why

El cliente costea sus productos con un modelo donde la **`cantidad` de cada ingrediente
es en realidad un FACTOR** (multiplicador adimensional) y agrega como "ingredientes"
ítems **operacionales** (arriendo, electricidad, HH de producción, desgaste de
maquinaria) que son *cost drivers*, no insumos físicos. Hoy esto provoca tres problemas:

1. La columna `cantidad` es `Numeric(10,3)` (3 decimales) y los factores del cliente
   requieren más precisión (4–8 decimales), por lo que el costo no calza con su Excel
   ("le faltan decimales en la cantidad").
2. El cálculo de costos asigna `Decimal` de alta precisión directo a columnas
   `Numeric` y, sin redondeo ni atomicidad, puede provocar `numeric field overflow`
   (un 500 que el frontend ve como "Failed to fetch" porque el middleware CORS no
   adjunta cabeceras en respuestas de error), dejando recetas a medias.
3. Los ítems operacionales se tratan como insumos físicos: producción **valida y
   descuenta stock** de ellos (pediría "stock de arriendo"), lo cual no tiene sentido.

## What Changes

- **Precisión de `cantidad`**: ampliar la columna a `Numeric(18,8)` (8 decimales) vía
  migración Alembic, para preservar los factores del cliente sin truncar.
- **Insumos operacionales vs. físicos**: agregar `afecta_inventario` (bool, default
  `true`) a `TipoProducto` y exponerlo en el mantenedor de Tipos de Producto del
  backoffice (ya existe como CRUD). No se crea un tipo nuevo: el cliente usa el tipo
  `SERVICIO` existente (o el que prefiera) marcándolo como que no afecta inventario.
  Producción SHALL **omitir validación y descuento de stock** para ingredientes cuyo
  tipo de producto no afecta inventario, pero SHALL seguir sumando su costo a la receta.
- **CORS en errores**: el `DynamicCORSMiddleware` adjuntará las cabeceras CORS también
  en respuestas de error (500/4xx), para que el frontend reciba el código/mensaje reales.
- **Cálculo de costos acotado**: `calcular_costos_receta` redondeará (`quantize`) los
  costos a la escala de su columna (2 decimales) antes de persistir, y validará los
  valores contra los límites de columna para no provocar overflow.
- **Persistencia atómica**: crear receta y crear/editar/eliminar ingrediente se harán
  en una sola transacción con `rollback` ante error, sin dejar estado inconsistente.

## Capabilities

### New Capabilities
- `api-cors`: Comportamiento de CORS de la API, incluyendo la garantía de que las
  respuestas de error también incluyen las cabeceras CORS adecuadas.
- `insumos-operacionales`: Distinción entre productos que afectan inventario (insumos
  físicos) y los operacionales (costo sin stock), y su efecto en producción.

### Modified Capabilities
- `recetas`: La `cantidad` del ingrediente se modela como factor de alta precisión
  (8 decimales); el cálculo de costos y la persistencia pasan a ser numéricamente
  acotados, redondeados y transaccionalmente atómicos, con validación de entrada.

## Impact

- **Base de datos (migraciones Alembic)**:
  - `ingredientes_receta.cantidad` → `Numeric(18,8)`.
  - `tipos_producto.afecta_inventario` (bool, default `true`). Sin seed de tipo nuevo.
- **Código backend**:
  - `main.py` → `DynamicCORSMiddleware.dispatch` (CORS en errores).
  - `routers/recetas.py` → `calcular_costos_receta`, `crear_receta` y handlers de
    ingredientes (quantize, validación, atomicidad/rollback).
  - `routers/produccion.py` → validación/descuento de stock omite insumos operacionales.
  - `schemas/receta.py` / `schemas/producto.py` → precisión de `cantidad`, flag de tipo.
  - `database/models.py` → `IngredienteReceta.cantidad`, `TipoProducto.afecta_inventario`.
- **Frontend (fme-backoffice)**: permitir ingresar `cantidad` con más decimales y mostrar
  el factor sin truncar; agregar la casilla "¿Afecta inventario?" en el mantenedor de
  Tipos de Producto. La corrección numérica de fondo es server-side.
- **Riesgo**: el cambio en el middleware CORS es transversal (probar éxito, preflight y
  error); cambiar el descuento de stock afecta el flujo de producción (probar OT con
  insumos mixtos físicos/operacionales).
