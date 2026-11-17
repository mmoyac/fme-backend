## Why

El módulo **Inventario** del backoffice (`/admin/inventario`) es central en la operación de Masas Estación y se construyó sin especificación. Tras la reunión con el cliente (2026-11-16), varias mejoras pedidas tocan este módulo (conteo, rediseño de transferencias, valorización). Antes de cambiarlo hace falta una línea base que documente qué hace hoy cada pestaña, para que los próximos changes se escriban como deltas sobre algo conocido.

## What Changes

- Se documenta como spec base el comportamiento **actual** de las pestañas del módulo Inventario:
  - **Existencias**: stock por producto y local, semáforo contra stock mínimo/crítico, vista consolidada del local WEB, búsqueda, filtro "solo alertas" y registro de **merma**.
  - **Transferencias**: traspaso directo de stock de un producto entre dos locales del tenant, con validaciones y registro del movimiento.
  - **Historial**: listado de movimientos de inventario del tenant con filtros por producto, local y tipo.
  - **Stock de Cajas** (botón del módulo): contador de cajas por producto y proveedor para carnes con lotes, alimentado por la recepción y consumido por pedidos de cajas y preventa.
  - **Solicitudes de transferencia** (menú Solicitudes): pedido de productos de un local a otro con flujo PENDIENTE → EN_PROCESO → FINALIZADO y recepción.
- Se documenta en `design.md` el **mapa del módulo**: cómo las piezas comparten el mismo stock y el mismo historial y cómo se complementan entre sí y con pedidos, producción y recepción.
- **Conteo** no se redocumenta aquí: está especificado en el change `add-conteo-inventario` (capability `inventario-conteo`); esta spec solo lo referencia como pestaña del módulo.
- Se registran en `design.md` las **brechas observadas** en el código (p. ej. transferencias que registran `usuario="admin"` fijo, cantidades solo enteras, historial limitado a 100 registros) como insumo para changes futuros. No se corrigen aquí.
- No se modifica código: es documentación retroactiva (baseline).

## Capabilities

### New Capabilities
- `inventario-existencias`: Consulta de stock por producto y local con semáforo de alertas, consolidado WEB y registro de merma.
- `inventario-transferencias`: Transferencia directa de stock de un producto entre dos locales del tenant.
- `inventario-historial`: Consulta del historial de movimientos de inventario con filtros.
- `inventario-stock-cajas`: Contador de cajas por producto/proveedor (carnes con lotes), sus entradas, salidas, vistas y ajuste manual.
- `inventario-solicitudes-transferencia`: Solicitudes de productos entre locales con aprobación, movimiento de stock y recepción.

### Modified Capabilities
<!-- Ninguna: no existen specs previas de inventario en openspec/specs/. `inventario-conteo` llega por add-conteo-inventario. -->

## Impact

- **Nuevos specs** (tras archivar): `openspec/specs/inventario-existencias/`, `inventario-transferencias/`, `inventario-historial/`.
- **Código de referencia (no se modifica)**:
  - Backend: `routers/inventario.py` (listado, ajuste-merma), `routers/movimientos_inventario.py` (transferencia, historial), `database/models.py` (`Inventario`, `MovimientoInventario`).
  - Backoffice: `app/admin/inventario/page.tsx` y `components/ExistenciasTab.tsx`, `TransferenciasTab.tsx`, `HistorialTab.tsx`; `lib/api/inventario.ts`, `lib/api/movimientos.ts`.
  - Stock de Cajas: `routers/stock_cajas.py`, `fme-backoffice/app/admin/inventario/stock-cajas/page.tsx`; flujos en `routers/enrolamiento.py`, `routers/pedidos.py`, `routers/preventa.py`.
  - Solicitudes: `routers/solicitudes_transferencia.py`, `fme-backoffice/app/admin/solicitudes/`, `components/solicitudes/`, `app/admin/dashboard/solicitudes/`.
- Fuera de alcance: Recepción/enrolamiento de lotes (módulo Recepción) más allá de su efecto en Stock de Cajas.
- Sin migraciones ni cambios de API.
