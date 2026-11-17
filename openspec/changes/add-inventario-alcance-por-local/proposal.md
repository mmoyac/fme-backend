## Why

Hoy cualquier usuario del backoffice (vendedor, producción, despachador) ve en Inventario el stock de **todos** los locales y puede registrar merma, transferir o contar en cualquiera de ellos. Lo esperado (definido con el usuario el 2026-11-16) es que un usuario de tienda opere solo sobre su local y que admin/superadmin vean y gestionen todos, con un selector de local. Solicitudes ya aplica esta regla; el resto del módulo no.

## What Changes

- **Regla de alcance**: un usuario tiene *alcance total* si es superadmin, tiene rol admin o no tiene local asignado; si no, su alcance es su **local asignado**.
- **Existencias**: alcance total → selector de local ("Todos los locales" + cada local), visible solo si hay más de un local físico; usuario de local → solo su local, sin selector y sin el consolidado WEB.
- **Merma, Transferencias y Conteo**: un usuario de local solo puede registrar merma, transferir **desde** su local e iniciar/operar conteos de su local; el backend responde 403 en otro caso.
- **Historial y lista de Conteos**: un usuario de local solo ve movimientos y conteos que involucran su local (filtrado en el backend).
- **Solicitudes**: el formulario sigue mostrando el stock del local al que se le pide, para que el usuario de tienda sepa a quién pedir sin ver Existencias de otros locales.
- La consulta general de inventario (`GET /api/inventario/`) **no** se restringe: la usan Pedidos, Producción, Productos, Cotizaciones y Alertas.

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-existencias`: agrega "Alcance por local en Existencias".
- `inventario-transferencias`: agrega "Transferir solo desde el local propio".
- `inventario-historial`: agrega "Historial limitado al local propio".
- `inventario-conteo`: agrega "Conteo limitado al local propio".
- `inventario-solicitudes-transferencia`: agrega "Stock del local origen al solicitar".

## Impact

- Backend: nuevo `utils/alcance_local.py`; `routers/inventario.py` (ajuste-merma), `routers/movimientos_inventario.py` (transferencia, historial), `services/conteo_inventario_service.py` (iniciar, listar y operar).
- Backoffice: `app/admin/inventario/page.tsx` y pestañas Existencias, Transferencias, Conteo.
- Depende de `add-conteo-inventario` y `document-inventario-baseline` (crean las capabilities). Compatible con `improve-inventario-existencias` (su filtro por local opera dentro del alcance). Sin migraciones.
