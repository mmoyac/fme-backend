## Context

`GET /api/movimientos/historial` (routers/movimientos_inventario.py) ya acepta `skip`, `limit`, `producto_id`, `local_id`, `tipo_movimiento`, filtra por tenant vía join con `Producto` y ordena por `fecha_movimiento DESC`. La UI (`HistorialTab.tsx`) no envía `skip/limit`, por eso corta en 100. `fecha_movimiento` es `timestamptz` con índice.

## Goals / Non-Goals

**Goals:** paginación, filtro por fechas, filtro de tipo completo, exportación Excel.

**Non-Goals:** cambiar cómo otros módulos registran movimientos; búsqueda de texto libre en notas; totales/agregados (valorización es otro change).

## Decisions

- **Paginación por offset con "Cargar más"** (no páginas numeradas): el uso típico es revisar lo reciente; el backend ya soporta `skip/limit`. Se agrega tope `limit ≤ 500`. Para saber si hay más, la UI pide `limit+1` y muestra el botón si llega el registro extra (sin cambiar el contrato de respuesta, que sigue siendo una lista).
  - *Alternativa*: respuesta `{items, total}` — rompe el contrato actual consumido por el backoffice.
- **Fechas**: parámetros `desde`/`hasta` como `date` (YYYY-MM-DD) interpretados en `America/Santiago`; `hasta` inclusivo (se filtra `< hasta + 1 día`).
- **Tipos dinámicos**: nuevo `GET /api/movimientos/tipos` → `SELECT DISTINCT tipo_movimiento` con join a productos del tenant. Etiquetas en un mapa del front; desconocidos se muestran tal cual.
- **Excel**: `GET /api/movimientos/historial/excel` reutiliza la misma construcción de query (función compartida), máx. 10.000 filas, openpyxl (dependencia agregada por `add-conteo-inventario`), fechas en hora de Chile.
- Endpoints `def` síncronos (regla del incidente 2026-11-11).

## Risks / Trade-offs

- [Offset lento con historiales muy grandes] → índice en `fecha_movimiento`; volumen actual bajo. Si crece, migrar a cursor por `(fecha, id)`.
- [Excel de 10.000 filas en memoria] → aceptable (~1–2 MB); se indica en el archivo si se truncó.

## Migration Plan

Sin migraciones. Deploy backend y luego backoffice. Archivar después de `document-inventario-baseline` y `add-conteo-inventario`.
