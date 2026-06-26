## Context

El módulo de compras (`fme-backend`, router `/api/compras`) persiste la cabecera en
la tabla `compras` y el detalle en `detalles_compra`. La columna `compras.monto_total`
es `Numeric(10, 2)` (tope `99.999.999,99`). En CLP, una compra al por mayor supera
fácilmente los 100 millones, lo que provoca `numeric field overflow` en PostgreSQL al
hacer `commit`. Como `create_compra`/`update_compra`/`recibir_compra` no envuelven el
`commit` en manejo de errores (a diferencia de `create_proveedor`), el error sube como
`500` opaco.

Otras columnas de totales del mismo modelo ya usan `Numeric(12, 2)` (comisiones,
`montos_*` de liquidaciones), por lo que ampliar las de compras a `Numeric(12, 2)`
alinea el modelo y elimina el límite práctico.

## Goals / Non-Goals

**Goals:**
- Eliminar el overflow ampliando las columnas monetarias del flujo de compras a
  `Numeric(12, 2)`.
- Reportar errores de persistencia como respuestas controladas con mensaje legible.
- Migración Alembic reversible aplicable en producción sin pérdida de datos.

**Non-Goals:**
- No se cambia el flujo de estados de compras (PENDIENTE → RECIBIDA).
- No se agrega reversión de stock ni estado ANULADA.
- No se rediseña el frontend (ya muestra `error.detail`).

## Decisions

- **Precisión `Numeric(12, 2)`**: cubre hasta ~$9.999.999.999, suficiente para CLP y
  consistente con columnas existentes. Alternativa descartada: `Numeric(14, 2)` —
  innecesariamente grande y no alineada con el resto del modelo.
- **Columnas a ampliar**: `compras.monto_total`, `detalles_compra.precio_unitario` y
  `productos.precio_compra`. Se incluye `precio_compra` porque al recibir una compra
  el `precio_unitario` (ya ampliado) se escribe en ese campo; dejarlo en `(10,2)`
  movería el overflow a la recepción.
- **Manejo de errores**: envolver el `db.commit()` de create/update/recibir en
  `try/except IntegrityError` + `except DataError` (psycopg2 mapea el overflow a
  `DataError`), haciendo `db.rollback()` y devolviendo `HTTPException(400, ...)` con
  mensaje legible. Se sigue el patrón ya usado en `create_proveedor`.
- **Migración**: usar `op.alter_column(..., type_=sa.Numeric(12, 2))` para cada columna;
  `downgrade` vuelve a `Numeric(10, 2)`.

## Risks / Trade-offs

- [El `downgrade` a `Numeric(10, 2)` fallaría si ya existen filas con montos > 100M] →
  Es el comportamiento esperado de un rollback de ampliación; se documenta que el
  downgrade solo es seguro si no se registraron montos grandes.
- [`ALTER COLUMN TYPE` sobre tablas grandes puede tomar un lock] → Las tablas de
  compras/productos son pequeñas en este tenant; el impacto es despreciable.
- [Capturar `Exception` genérico ocultaría bugs reales] → Se capturan solo
  `IntegrityError` y `DataError`; cualquier otra excepción sigue propagándose.

## Migration Plan

1. Aplicar el cambio de modelo y la migración en desarrollo (`alembic upgrade head`).
2. Verificar en dev: crear/recibir una compra con `monto_total > 100M` y confirmar
   que persiste; provocar un error (p. ej. FK inválida) y confirmar respuesta 400.
3. Una vez validado en dev, promover a producción (push a `main`; el entrypoint corre
   las migraciones automáticamente).
4. Rollback: `alembic downgrade -1` (seguro solo si no se registraron montos > 100M).
