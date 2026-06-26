## Why

Al crear (o recibir) una compra de monto alto, el backoffice muestra "Error interno
del servidor" (500). La causa raíz es que `Compra.monto_total` está definido como
`Numeric(10, 2)` (tope ~$99.999.999 CLP); cuando la suma de las líneas supera ese
límite, PostgreSQL lanza `numeric field overflow`. Como `create_compra` (y `update`/
`recibir`) no capturan errores de base de datos, el fallo se propaga como un 500
opaco en lugar de un mensaje legible. Para montos en CLP de compras al por mayor,
ese tope es demasiado bajo.

## What Changes

- Ampliar las columnas monetarias del flujo de compras de `Numeric(10, 2)` a
  `Numeric(12, 2)` (tope ~$9.999.999.999), consistente con otras columnas de totales
  del modelo (comisiones ya usan `Numeric(12, 2)`):
  - `compras.monto_total`
  - `detalles_compra.precio_unitario`
  - `productos.precio_compra` (recibe el precio de costo al recibir una compra)
- Crear una migración Alembic que altere esas columnas en la base de datos.
- Agregar manejo de errores en `create_compra`, `update_compra` y `recibir_compra`
  para devolver un `400`/`422` con mensaje legible en vez de un `500` opaco cuando
  falla la persistencia (overflow, FK inválida, etc.).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `compras`: se ajustan los requisitos de creación/recepción para garantizar que
  montos altos se persistan correctamente y que los errores de persistencia se
  reporten con un mensaje legible en lugar de un error interno genérico.

## Impact

- **Código backend**: `database/models.py` (tipos de columna), `routers/compras.py`
  (manejo de errores).
- **Migraciones**: nueva revisión Alembic en `migrations/versions/`.
- **Base de datos producción**: `ALTER COLUMN` de tipo numérico en 3 columnas
  (ampliación de precisión, sin pérdida de datos).
- **Frontend**: sin cambios; ya muestra `error.detail` cuando el backend responde un
  error controlado.
- **Compatibilidad**: no breaking. Ampliar precisión numérica es retrocompatible.
