## Why

Al documentar el módulo de inventario (`document-inventario-baseline`) se encontraron endpoints que **no exigen autenticación** o **no filtran por tenant**: cualquier persona en internet puede leer, crear o borrar solicitudes de transferencia, y un usuario de un tenant puede ajustar el stock de cajas de otro conociendo los IDs. En un sistema multi-tenant en producción esto es una exposición de datos y de integridad del stock; se corrige antes que cualquier mejora funcional.

## What Changes

- **Solicitudes de transferencia**: todos los endpoints exigen usuario autenticado y operan solo sobre el tenant del usuario (`current_user.tenant_id`, no el hostname). Al crear, `tenant_id`, solicitante y estado inicial (`PENDIENTE`) los fija el servidor; los valores enviados por el cliente se ignoran. Eliminar exige ser admin o el solicitante.
- **Stock de Cajas**: `PUT /ajustar`, `POST /actualizar-desde-enrolamiento` y `POST /reservar-para-pedido` validan que el producto pertenezca al tenant del usuario (404 si no).
- **BREAKING** para clientes que llamen a esos endpoints sin token: ahora reciben 401. El backoffice ya envía token, no se ve afectado.

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-solicitudes-transferencia`: agrega requisito de autenticación, aislamiento por tenant y datos fijados por el servidor.
- `inventario-stock-cajas`: agrega requisito de aislamiento por tenant en las operaciones de escritura.

## Impact

- Backend: `routers/solicitudes_transferencia.py`, `main.py` (dependencia de auth en el router), `routers/stock_cajas.py`.
- Backoffice: `components/solicitudes/SolicitudForm.tsx` deja de enviar `tenant_id`/`usuario_solicitante_id`/`estado_id` (el servidor los ignora igual).
- Depende de `document-inventario-baseline` (crea las capabilities). Es independiente del resto de mejoras y **se puede desplegar primero**.
