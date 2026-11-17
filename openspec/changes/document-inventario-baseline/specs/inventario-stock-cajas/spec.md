# Spec Delta

## Purpose

Lleva el contador de cajas disponibles por producto y proveedor para productos de peso variable (carnes) que se reciben como lotes, permite consultarlo y ajustarlo manualmente, y registra sus movimientos. Es un stock paralelo al de la tabla de inventario por local.

## ADDED Requirements

### Requirement: Contador de cajas por producto y proveedor
El sistema SHALL mantener un registro por par producto/proveedor con cajas disponibles, total de cajas recibidas, total de cajas vendidas y fecha de última actualización. Este contador MUST NOT afectar ni reflejarse en el stock por local de Existencias.

#### Scenario: Cajas no aparecen en Existencias
- **GIVEN** un producto de carne con 12 cajas disponibles de un proveedor
- **WHEN** el usuario mira el producto en Existencias
- **THEN** el stock por local no incluye esas 12 cajas

### Requirement: Entrada de cajas desde la recepción
Al finalizar un enrolamiento de recepción, el sistema SHALL marcar sus lotes como disponibles para la venta y, para productos de la categoría "CARNES", sumar una caja por lote al contador del par producto/proveedor (creándolo si no existe) y registrar un movimiento `ENTRADA_ENROLAMIENTO`.

#### Scenario: Enrolamiento finalizado
- **GIVEN** un enrolamiento con 5 lotes de un producto de categoría CARNES del proveedor X
- **WHEN** el enrolamiento pasa a FINALIZADO
- **THEN** las cajas disponibles y las recibidas del par producto/X aumentan en 5 y existe un movimiento `ENTRADA_ENROLAMIENTO`

### Requirement: Salida de cajas por pedidos y preventa
Los pedidos de cajas variables y la preventa SHALL tomar lotes disponibles en orden FIFO por fecha de vencimiento, reservarlos (movimiento `RESERVA_LOTE`) descontando cajas disponibles, y al confirmarse la venta marcarlos vendidos (movimiento `VENTA_LOTE`) sumando a cajas vendidas. La cancelación SHALL liberar los lotes y devolver las cajas disponibles.

#### Scenario: Pedido de cajas confirmado
- **GIVEN** 10 cajas disponibles y un pedido de 2 cajas
- **WHEN** se crea y luego se confirma el pedido
- **THEN** quedan 8 cajas disponibles, 2 lotes vendidos y existen movimientos `RESERVA_LOTE` y `VENTA_LOTE`

#### Scenario: Pedido cancelado
- **WHEN** se cancela un pedido con 2 lotes reservados
- **THEN** los 2 lotes vuelven a estar disponibles y las cajas disponibles aumentan en 2

### Requirement: Vistas de Stock de Cajas
La pantalla Stock de Cajas SHALL ofrecer tres vistas: **Resumen** (total de cajas disponibles, productos con registro, proveedores con registro, pares sin stock y los productos con más stock), **Stock Detallado** (producto, proveedor, stock actual, recibidas, vendidas y última actualización, con opción "Solo mostrar con stock disponible") y **Movimientos** (los 50 más recientes con fecha, producto, proveedor, tipo, cajas, antes → después y usuario).

#### Scenario: Filtrar con stock
- **WHEN** el usuario activa "Solo mostrar con stock disponible" en Stock Detallado
- **THEN** solo se listan pares con cajas disponibles mayores a 0

### Requirement: Ajuste manual de cajas
Desde Stock Detallado el usuario SHALL poder fijar las cajas disponibles de un par producto/proveedor; el sistema MUST registrar un movimiento `AJUSTE_INVENTARIO` con la diferencia, las cajas antes y después y el usuario.

#### Scenario: Ajuste
- **GIVEN** 10 cajas disponibles
- **WHEN** el usuario ajusta a 8
- **THEN** quedan 8 cajas y existe un movimiento `AJUSTE_INVENTARIO` de −2 con antes 10 y después 8

### Requirement: Acceso al módulo de cajas
Stock de Cajas SHALL estar disponible solo para tenants con el módulo "preventa" habilitado y usuarios autenticados, y sus consultas MUST mostrar solo productos del tenant del usuario.

#### Scenario: Tenant sin módulo preventa
- **WHEN** un usuario de un tenant sin el módulo preventa consulta Stock de Cajas
- **THEN** el sistema responde 403
