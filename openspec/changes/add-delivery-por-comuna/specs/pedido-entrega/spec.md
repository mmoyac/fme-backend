# Spec Delta

## MODIFIED Requirements

### Requirement: Modalidad de entrega del pedido

Todo pedido SHALL tener una `modalidad_entrega` con valor `RETIRO` (el cliente lo retira en el local) o `DESPACHO` (se le envía). La modalidad SHALL elegirse al aceptar una cotización, al crear un pedido en el backoffice y en el checkout de la tienda online, y SHALL guardarse en el pedido.

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
- **WHEN** un cliente crea un pedido desde la tienda online (landing) y elige retiro en casa central o delivery
- **THEN** el pedido queda con `modalidad_entrega = RETIRO` o `DESPACHO` según su elección

#### Scenario: Cambio manual a ENTREGADO
- **WHEN** un usuario cambia el estado de un pedido a ENTREGADO desde Pedidos
- **THEN** el sistema también registra `fecha_entrega` y `entregado_por_id`, si aún no estaban
