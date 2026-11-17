# Proposal

## Why

Hoy el pedido no guarda si el cliente lo **retira en el local** o si se le **despacha**. La marca "requiere delivery" que se elige al aceptar una cotización o al crear un pedido no se persiste (solo queda `costo_delivery`, si lo hubo). Un pedido de retiro pasa a ENTREGADO cambiando el estado a mano, sin registrar quién lo entregó, cuándo ni quién lo retiró. El usuario necesita **monitorear cómo y cuándo se entregó cada pedido**, sobre todo en ventas a crédito que aparecen en Cobranza (ej. pedido #00127, "Transferencia a 30 días").

## What Changes

- Nuevo campo `modalidad_entrega` en el pedido (`RETIRO` | `DESPACHO`), más los datos de entrega: `fecha_entrega`, `entregado_por_id` (usuario), `retirado_por_nombre`, `retirado_por_rut` y `nota_entrega`.
- La modalidad se elige y **se guarda** al aceptar una cotización y al crear un pedido en el backoffice. `requiere_delivery = true` equivale a `DESPACHO`.
- Nueva acción **"Marcar retirado"** (`POST /api/pedidos/{id}/retiro`): solo para pedidos `RETIRO` en estado CONFIRMADO o EN_PREPARACION. Los pasa a ENTREGADO y registra quién lo entregó, cuándo y, opcionalmente, quién lo retiró.
- Despacho mantiene su flujo (hoja de ruta / despacho → ENTREGADO), pero ahora también registra `fecha_entrega` y `entregado_por_id` en el pedido.
- La venta POS directa (entrega inmediata) queda como `RETIRO`, entregada en el acto por el vendedor.
- **Pedidos**: columna y filtro de modalidad, con el detalle de la entrega. **Cobranza**: modalidad y fecha de entrega en cada cobro.
- Backfill de los pedidos existentes.

## Capabilities

### New Capabilities
- `pedido-entrega`: modalidad de entrega del pedido (retiro/despacho), el registro de la entrega (quién, cuándo, quién retiró) y su visibilidad en Pedidos y Cobranza.

### Modified Capabilities
<!-- `despacho` no tiene requirements formales todavía; el cambio sobre su flujo se especifica dentro de `pedido-entrega`. -->

## Impact

- **BD**: migración que agrega columnas a `pedidos` y hace el backfill.
- **Backend**: `routers/pedidos.py` (crear pedido backoffice/POS, nuevo endpoint de retiro, filtros y respuestas), `routers/cotizaciones.py` (aceptar), `routers/hojas_ruta.py` y `routers/despachos.py` (registrar la entrega), `routers/cobranza.py` (exponer modalidad y fecha), schemas de pedido.
- **Backoffice**: aceptar cotización (selector de modalidad), lista y detalle de Pedidos (columna, filtro, botón "Marcar retirado" con modal), Cobranza (columnas).
- Sin cambios incompatibles: los campos nuevos son opcionales en las APIs existentes.
