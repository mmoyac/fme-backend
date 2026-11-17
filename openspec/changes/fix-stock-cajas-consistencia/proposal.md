## Why

El contador de cajas por producto/proveedor se mantiene a mano desde recepción, pedidos y preventa, y hoy puede descuadrarse respecto a los lotes reales: el ajuste manual acepta negativos y no actualiza la fecha, los pedidos pueden dejarlo negativo, se ofrecen lotes ya reservados en preventa, y sus movimientos se ven como "0 → 0" y "+1" aunque sean salidas. Además el resumen tiene etiquetas engañosas y los listados se truncan sin aviso. Ver brechas en `document-inventario-baseline/design.md`.

## What Changes

- **Ajuste manual**: cantidad entera ≥ 0 y motivo obligatorio; actualiza la fecha de última actualización; la UI muestra el mensaje real del backend.
- **Contador nunca negativo**: pedidos y preventa validan cajas disponibles antes de reservar.
- **Lotes disponibles** excluyen los reservados (preventa) y respetan el proveedor cuando se indica.
- **Movimientos completos**: toda reserva, venta, devolución y liberación (incluida la de preventa) registra signo correcto y cajas antes → después.
- **Entrada desde recepción**: cuenta todos los lotes del enrolamiento (no solo la categoría con nombre exacto "CARNES").
- **Vistas**: etiquetas correctas en el resumen, búsqueda por producto/proveedor y paginación en Stock Detallado y Movimientos, etiquetas para todos los tipos.
- **Reconciliación**: endpoint que compara el contador con los lotes disponibles reales y lista diferencias.

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-stock-cajas`: cambian "Entrada de cajas desde la recepción", "Salida de cajas por pedidos y preventa", "Vistas de Stock de Cajas" y "Ajuste manual de cajas"; se agrega "Reconciliación contra lotes".

## Impact

- Backend: `routers/stock_cajas.py`, `schemas/stock_cajas.py`, `routers/pedidos.py` (rama CAJAS_VARIABLES), `routers/preventa.py`, `routers/enrolamiento.py` (`actualizar_stock_cajas_desde_enrolamiento`).
- Backoffice: `app/admin/inventario/stock-cajas/page.tsx`.
- Depende de `fix-seguridad-inventario` (tenant en escrituras). Sin migraciones (los campos ya existen).
