## Why

Existencias es la foto del stock, pero hoy mezcla productos inactivos y operacionales (arriendo, luz, HH, que no manejan stock), carga como máximo 1000 productos y no se puede exportar. En la minuta del cliente (2026-11-16) se pidió "exportar a Excel la información por tienda, categoría e inventario bajo". Ver brechas en `document-inventario-baseline/design.md`.

## What Changes

- Existencias muestra solo **productos activos que manejan stock** (tipo de producto con `afecta_inventario = true`), sin tope de 1000, con los locales en orden alfabético y el local WEB al final.
- **Filtros nuevos**: por categoría y por local, además de búsqueda y "Solo mostrar alertas".
- **Exportar a Excel** lo que se ve en pantalla con los filtros aplicados: una fila por producto y local con categoría, unidad, stock, mínimo, crítico y estado del semáforo.
- El cálculo de existencias y semáforo se hace en un **endpoint del backend** que usan la pantalla y el Excel (una sola regla).

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-existencias`: cambian "Stock por producto y local" (solo activos que manejan stock, sin tope, orden de locales) y "Búsqueda y filtro de alertas" (categoría y local); se agrega "Exportar existencias a Excel".

## Impact

- Backend: `routers/inventario.py` — nuevos `GET /inventario/existencias` y `GET /inventario/existencias/excel` (openpyxl, agregado por `add-conteo-inventario`).
- Backoffice: `ExistenciasTab.tsx`, `lib/api/inventario.ts`.
- Archivar después de `document-inventario-baseline` y `fix-inventario-movimientos-trazabilidad` (que modifica otro requisito de la misma capability). Sin migraciones.
