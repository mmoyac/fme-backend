## ADDED Requirements

### Requirement: Modalidad de entrega del pedido

Todo pedido SHALL tener una `modalidad_entrega` con valor `RETIRO` (el cliente lo retira en el local) o `DESPACHO` (se le envía). La modalidad SHALL elegirse al aceptar una cotización y al crear un pedido en el backoffice, y SHALL guardarse en el pedido.

#### Scenario: Aceptar cotización con delivery
- **WHEN** se acepta una cotización con `requiere_delivery = true` (o `modalidad_entrega = DESPACHO`)
- **THEN** el pedido creado queda con `modalidad_entrega = DESPACHO`

#### Scenario: Aceptar cotización sin delivery
- **WHEN** se acepta una cotización sin delivery
- **THEN** el pedido creado queda con `modalidad_entrega = RETIRO`

#### Scenario: Venta POS con entrega inmediata
- **WHEN** se crea un pedido POS directo que se confirma y entrega en el acto
- **THEN** el pedido queda con `modalidad_entrega = RETIRO`, `fecha_entrega` = ahora y `entregado_por_id` = el vendedor

#### Scenario: Pedido de la tienda online
- **WHEN** un cliente crea un pedido desde la tienda online (landing), que no ofrece retiro
- **THEN** el pedido queda con `modalidad_entrega = DESPACHO`

#### Scenario: Cambio manual a ENTREGADO
- **WHEN** un usuario cambia el estado de un pedido a ENTREGADO desde Pedidos
- **THEN** el sistema también registra `fecha_entrega` y `entregado_por_id`, si aún no estaban

### Requirement: Marcar un pedido como retirado

El sistema SHALL exponer `POST /api/pedidos/{id}/retiro`, autenticado y aislado por tenant, para registrar que el cliente retiró un pedido `RETIRO` en estado CONFIRMADO o EN_PREPARACION. La acción pasa el pedido a ENTREGADO y guarda `fecha_entrega`, `entregado_por_id` (usuario actual) y, si se informan, `retirado_por_nombre`, `retirado_por_rut` y `nota_entrega`.

#### Scenario: Retiro registrado
- **WHEN** un usuario marca como retirado un pedido RETIRO CONFIRMADO, indicando "Juan Pérez"
- **THEN** el pedido queda ENTREGADO, con fecha de entrega, el usuario que lo entregó y "Juan Pérez" como quien retiró

#### Scenario: Pedido de despacho
- **WHEN** se intenta marcar como retirado un pedido `DESPACHO`
- **THEN** el sistema responde `400` "Este pedido es de despacho; se entrega desde la hoja de ruta"

#### Scenario: Pedido aún no listo
- **WHEN** se intenta marcar como retirado un pedido PENDIENTE (por ejemplo, esperando producción), ENTREGADO o CANCELADO
- **THEN** el sistema responde `400` y el pedido no cambia

### Requirement: Registro de la entrega en despacho

Cuando un pedido `DESPACHO` se marca como entregado desde la hoja de ruta o desde el despacho, el sistema SHALL guardar en el pedido `fecha_entrega` y `entregado_por_id`, además de pasarlo a ENTREGADO como hasta ahora.

#### Scenario: Entrega desde hoja de ruta
- **WHEN** el despachador marca entregado un ítem de la hoja de ruta
- **THEN** el pedido queda ENTREGADO, con `fecha_entrega` y `entregado_por_id` = el despachador

### Requirement: Monitoreo de la entrega en Pedidos y Cobranza

La lista de pedidos SHALL mostrar la modalidad de entrega y permitir filtrar por ella (`modalidad_entrega`) y por estado de entrega (`entregado` true/false). El detalle del pedido SHALL mostrar fecha de entrega, quién entregó y quién retiró. Cada cobro de Cobranza SHALL incluir la `modalidad_entrega` y la `fecha_entrega` de su pedido.

#### Scenario: Criterio de entregado en el filtro
- **WHEN** se filtra con `entregado=true`
- **THEN** se incluyen los pedidos con `fecha_entrega` o en estado ENTREGADO (incluidos pedidos antiguos sin fecha); con `entregado=false` se excluyen además los CANCELADO

#### Scenario: Retiros pendientes
- **WHEN** el usuario filtra Pedidos por modalidad RETIRO y no entregados
- **THEN** ve los pedidos que el cliente aún no retira

#### Scenario: Cobro de un pedido retirado
- **WHEN** el usuario revisa en Cobranza el cobro de un pedido retirado
- **THEN** ve "Retiro" y la fecha en que se entregó

### Requirement: Backfill de pedidos existentes

La migración SHALL asignar `modalidad_entrega` a los pedidos existentes: `DESPACHO` si tienen `costo_delivery`, un despacho o un ítem de hoja de ruta; `RETIRO` en los demás casos. Para pedidos ya ENTREGADO SHALL copiar la fecha de entrega disponible (de la hoja de ruta o del despacho), dejando nulo lo que no se conoce.

#### Scenario: Pedido histórico en hoja de ruta
- **WHEN** se aplica la migración sobre un pedido que estuvo en una hoja de ruta y fue entregado
- **THEN** queda con `modalidad_entrega = DESPACHO` y la `fecha_entrega` del ítem de la hoja de ruta
