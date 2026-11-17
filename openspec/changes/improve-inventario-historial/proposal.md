## Why

El Historial de inventario es la herramienta de auditoría del módulo (quién movió qué stock, cuándo y dónde), pero hoy solo muestra los últimos 100 movimientos, no filtra por fecha, su filtro de tipo ofrece 6 de los ~13 tipos que el sistema registra y no se puede exportar. El cliente pidió explícitamente poder exportar a Excel la información de inventario (reunión 2026-11-16). Ver brechas en `document-inventario-baseline/design.md`.

## What Changes

- **Paginación**: el historial carga por páginas ("Cargar más") en lugar de cortar en 100 registros.
- **Filtro por rango de fechas** (desde / hasta), combinable con producto, local y tipo.
- **Filtro de tipo dinámico**: las opciones salen de los tipos realmente registrados en el tenant; todos los tipos conocidos tienen etiqueta legible.
- **Exportar a Excel** el historial con los filtros aplicados.
- Sin cambios en cómo se registran los movimientos.

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-historial`: cambia "Volumen del historial" (paginado), "Filtros del historial" (agrega fechas), "Tipos de movimiento" (filtro dinámico y etiquetas para todos los tipos) y agrega "Exportar historial a Excel".

## Impact

- **Depende de** `document-inventario-baseline` (crea `inventario-historial`) y de `add-conteo-inventario` (aporta `openpyxl` y el tipo `AJUSTE_CONTEO`). Archivar después de ambos.
- Backend: `routers/movimientos_inventario.py` (parámetros `desde`/`hasta`, tope de `limit`, endpoints nuevos `GET /movimientos/tipos` y `GET /movimientos/historial/excel`).
- Backoffice: `HistorialTab.tsx`, `lib/api/movimientos.ts`.
- Sin migraciones. Compatibilidad: los parámetros nuevos son opcionales; `GET /movimientos/historial` sigue respondiendo una lista.
