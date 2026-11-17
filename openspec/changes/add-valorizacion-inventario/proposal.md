# Proposal

## Why

En la reunión del 16-11-26 (punto 1.1.9 del resumen) el cliente pidió tener en EffiChain la **valorización del inventario** que hoy usa en Loyverse: cuánto dinero tiene inmovilizado en stock, a costo y a precio de venta, por local y categoría. Hoy EffiChain solo guarda el **último** costo de compra (cada compra recibida sobrescribe `precio_compra`), así que una sola compra cara o barata distorsiona el valor de todo el stock. Además no existe ningún reporte que cruce stock × costo × precio.

## What Changes

- Nuevo campo `costo_promedio` (neto, por unidad de inventario) en `Producto`. Es un **promedio ponderado global por producto**, igual que en Loyverse, y se inicializa con `precio_compra` o, si no hay, con `costo_fabricacion`.
- El costo promedio se recalcula al **recibir una compra** (respetando `factor_conversion_compra`) y al **finalizar una producción**, donde el producto terminado entra con su `costo_fabricacion`. `precio_compra` sigue guardando el último costo.
- Nuevo endpoint `GET /api/inventario/valorizacion` que entrega, por producto y local: stock, costo promedio, valor inventario (stock × costo), valor venta (stock × precio neto del local), ganancia potencial y margen. Incluye totales y filtros por local, categoría y búsqueda. Respeta el alcance por local del usuario.
- Nuevo endpoint `GET /api/inventario/valorizacion/excel` que exporta lo mismo a `.xlsx`.
- Nueva pestaña **Valorización** en Inventario (fme-backoffice), con tarjetas de totales, tabla, filtros y botón Exportar a Excel.
- Los productos sin costo o sin precio aparecen marcados ("Sin costo" / "Sin precio"), no se ocultan, para que el cliente pueda completarlos.

## Capabilities

### New Capabilities
- `inventario-valorizacion`: costo promedio ponderado por producto, el reporte de valorización de inventario (a costo y a venta) y su exportación a Excel.

### Modified Capabilities
- `compras`: al recibir una compra, además del `precio_compra` se actualiza el `costo_promedio` ponderado del producto.

## Impact

- **BD**: migración Alembic que agrega `productos.costo_promedio NUMERIC(12,4) NULL` y lo inicializa (backfill).
- **Backend**: `routers/compras.py` (recibir), `routers/produccion.py` (finalizar orden), nuevo servicio `services/costo_promedio.py`, `routers/inventario.py` (endpoints de valorización), schemas, dependencia `openpyxl` en `requirements.txt`.
- **Backoffice**: `app/admin/inventario/page.tsx` (nueva pestaña), nuevo `components/ValorizacionTab.tsx`, `lib/api/valorizacion.ts`.
- **Seguridad**: aislamiento por tenant y `utils/alcance_local` (el usuario de tienda solo ve su local).
- Sin cambios incompatibles en las APIs existentes.
