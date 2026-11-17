# Proposal

## Why

Hoy cualquier usuario autenticado puede crear y finalizar Órdenes de Producción (OP): los permisos son solo de menú y los endpoints no validan rol. El negocio necesita separar responsabilidades: el **admin pide** la fabricación (ej. 4 cajas de empanadas) y **producción informa lo que realmente salió** (4, o menos). Sin esa separación no hay trazabilidad de quién pidió, quién produjo, ni cuánto se perdió.

## What Changes

- Nuevo rol `produccion` en cada tenant (creado por migración, con acceso al menú Producción).
- Validación de rol en backend para OP:
  - Crear OP (`POST /produccion/ordenes`, y OT tipo OP en `POST /ordenes-trabajo`): solo roles administradores (`admin`, `administrador`, `superadmin`).
  - Finalizar OP (`POST /produccion/ordenes/{id}/finalizar`): rol `produccion` o roles administradores.
  - Eliminar OP: solo roles administradores.
  - **BREAKING**: usuarios con rol `vendedor`/`tesorero` que hoy crean o finalizan OP manualmente recibirán 403.
- La OP finaliza con lo realmente producido; no queda saldo pendiente ni se genera una OP complementaria.
- Trazabilidad: `ordenes_produccion.solicitado_por_id` y `ordenes_produccion.producido_por_id` (FK a `users`).
- Diferencia programada vs producida por detalle, y `motivo_diferencia` opcional por detalle cuando se produce menos.
- Backoffice: vista de "OP pendientes" para el rol `produccion` con captura de cantidad real y motivo; el detalle de OP muestra solicitado por / producido por y la diferencia.
- Las OP generadas automáticamente al aceptar una cotización siguen creándose sin restricción de rol (registran `solicitado_por_id` = usuario que acepta).

## Capabilities

### New Capabilities
- `produccion`: Ciclo de vida de la Orden de Producción (solicitud, finalización con cantidades reales, diferencias) y los permisos por rol sobre ella.

### Modified Capabilities
<!-- Ninguna: no existe spec previa de producción (specs actuales: compras, despacho, recetas). -->

## Impact

- **fme-backend**: `database/models.py` (OrdenProduccion, DetalleOrdenProduccion), `schemas/produccion.py`, `routers/produccion.py`, `routers/ordenes_trabajo.py` (creación OT tipo OP), `routers/cotizaciones.py` (setear solicitado_por_id), nuevo helper de verificación de rol, migración Alembic (columnas + rol `produccion` por tenant + permiso de menú).
- **fme-backoffice**: `app/admin/produccion/page.tsx`, `lib/api/produccion.ts` (tipos y payload de finalización), ocultar acciones crear/eliminar al rol `produccion`.
- Usuarios: el admin del tenant debe asignar el rol `produccion` a los usuarios de cocina.
