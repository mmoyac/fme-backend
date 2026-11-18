## ADDED Requirements

### Requirement: Resumen de pedidos por entregar
El sistema SHALL exponer `GET /api/dashboard/por-entregar` con la cantidad y el monto de pedidos del tenant en estado CONFIRMADO, EN_PREPARACION y EN_RUTA, más la cantidad de pedidos pagados que siguen PENDIENTE (pagados en línea sin confirmar). El dashboard del backoffice SHALL mostrarlo en la tarjeta "Por entregar", y cada número SHALL abrir la lista de Pedidos filtrada.

#### Scenario: Pagados sin confirmar
- **WHEN** hay al menos un pedido pagado en estado PENDIENTE
- **THEN** la métrica "Pagados sin confirmar" se resalta en ámbar
- **AND** al hacer clic abre Pedidos con `?estado=PENDIENTE&pagado=si`

### Requirement: Filtros del listado de pedidos
El listado de pedidos (`GET /api/pedidos/`) SHALL aceptar el filtro `pagado` (true/false). La pantalla de Pedidos SHALL ofrecer el estado EN_RUTA y el filtro de pago, y SHALL tomar los filtros iniciales desde la URL (`estado`, `pagado`).

#### Scenario: Enlace desde el dashboard
- **WHEN** se abre `/admin/pedidos?estado=PENDIENTE&pagado=si`
- **THEN** la lista muestra solo los pedidos pendientes que ya están pagados

### Requirement: Origen de los pedidos de la tienda
El listado de pedidos SHALL incluir el canal de venta (`canal_venta_codigo`, `canal_venta_nombre`). En la columna "Creado por", los pedidos sin usuario del backoffice SHALL mostrar "🛒 Tienda online" si vienen de la landing, el nombre del canal si vienen de otro, o "Sin registro" si no tienen canal.

#### Scenario: Pedido hecho por el cliente en la landing
- **WHEN** un pedido del canal LANDING no tiene usuario creador
- **THEN** la columna "Creado por" muestra "🛒 Tienda online"
