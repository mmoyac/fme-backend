## MODIFIED Requirements

### Requirement: Entrada de cajas desde la recepción
Al finalizar un enrolamiento de recepción, el sistema SHALL marcar sus lotes como disponibles para la venta y sumar una caja por lote al contador del par producto/proveedor (creándolo si no existe), sin depender del nombre de la categoría, y registrar un movimiento `ENTRADA_ENROLAMIENTO` con cajas antes y después. Un enrolamiento ya finalizado MUST NOT volver a sumar sus lotes.

#### Scenario: Enrolamiento finalizado
- **GIVEN** un enrolamiento con 5 lotes de un producto del proveedor X
- **WHEN** el enrolamiento pasa a FINALIZADO
- **THEN** las cajas disponibles y las recibidas del par producto/X aumentan en 5 y existe un movimiento `ENTRADA_ENROLAMIENTO` con antes y después

#### Scenario: Finalizar dos veces
- **WHEN** se intenta finalizar de nuevo un enrolamiento ya FINALIZADO
- **THEN** el contador no cambia

### Requirement: Salida de cajas por pedidos y preventa
Los pedidos de cajas variables y la preventa SHALL tomar lotes disponibles no reservados en orden FIFO por fecha de vencimiento, reservarlos (movimiento `RESERVA_LOTE`) descontando cajas disponibles, y al confirmarse la venta marcarlos vendidos (movimiento `VENTA_LOTE`) sumando a cajas vendidas. Si no hay cajas suficientes MUST rechazarse sin dejar el contador negativo. La cancelación o el retiro de un ítem SHALL liberar los lotes, devolver las cajas disponibles y registrar el movimiento correspondiente. Todo movimiento MUST registrar el signo correcto y las cajas antes y después.

#### Scenario: Pedido de cajas confirmado
- **GIVEN** 10 cajas disponibles y un pedido de 2 cajas
- **WHEN** se crea y luego se confirma el pedido
- **THEN** quedan 8 cajas disponibles, 2 lotes vendidos y existen movimientos `RESERVA_LOTE` (−1 cada uno, con antes y después) y `VENTA_LOTE`

#### Scenario: Pedido cancelado
- **WHEN** se cancela un pedido con 2 lotes reservados
- **THEN** los 2 lotes vuelven a estar disponibles, las cajas disponibles aumentan en 2 y se registran los movimientos de liberación

#### Scenario: Cajas insuficientes
- **GIVEN** 1 caja disponible
- **WHEN** se intenta crear un pedido de 3 cajas
- **THEN** el sistema lo rechaza y el contador sigue en 1

#### Scenario: Lote reservado en preventa
- **GIVEN** un lote reservado por una preventa
- **WHEN** se consultan los lotes disponibles para un pedido
- **THEN** ese lote no aparece

### Requirement: Vistas de Stock de Cajas
La pantalla Stock de Cajas SHALL ofrecer tres vistas: **Resumen** (total de cajas disponibles, productos con cajas disponibles, proveedores con cajas disponibles, pares sin stock y los productos con más stock), **Stock Detallado** (producto, proveedor, stock actual, recibidas, vendidas y última actualización, con búsqueda por producto o proveedor, opción "Solo mostrar con stock disponible" y paginación) y **Movimientos** (paginados, con fecha, producto, proveedor, tipo con etiqueta legible, cajas con signo, antes → después y usuario). Los errores del backend MUST mostrarse al usuario.

#### Scenario: Filtrar con stock
- **WHEN** el usuario activa "Solo mostrar con stock disponible" en Stock Detallado
- **THEN** solo se listan pares con cajas disponibles mayores a 0

#### Scenario: Más de 100 pares
- **GIVEN** existen 150 pares producto/proveedor
- **WHEN** el usuario recorre Stock Detallado
- **THEN** puede ver los 150 mediante paginación

### Requirement: Ajuste manual de cajas
Desde Stock Detallado el usuario SHALL poder fijar las cajas disponibles de un par producto/proveedor en un entero mayor o igual a 0 indicando un motivo; el sistema MUST actualizar la fecha de última actualización y registrar un movimiento `AJUSTE_INVENTARIO` con la diferencia, las cajas antes y después, el motivo y el usuario.

#### Scenario: Ajuste
- **GIVEN** 10 cajas disponibles
- **WHEN** el usuario ajusta a 8 con motivo "Caja dañada"
- **THEN** quedan 8 cajas, la fecha de actualización cambia y existe un movimiento `AJUSTE_INVENTARIO` de −2 con antes 10, después 8 y el motivo

#### Scenario: Ajuste negativo
- **WHEN** el usuario intenta ajustar a −1
- **THEN** el sistema responde 400 con el mensaje y la pantalla lo muestra

## ADDED Requirements

### Requirement: Reconciliación contra lotes
El sistema SHALL ofrecer una consulta que compare, por par producto/proveedor del tenant, las cajas disponibles del contador con la cantidad de lotes disponibles, no reservados y no vendidos, y liste los pares con diferencia.

#### Scenario: Contador descuadrado
- **GIVEN** el contador indica 10 cajas y existen 9 lotes disponibles para ese par
- **WHEN** el usuario consulta la reconciliación
- **THEN** el par aparece con contador 10, lotes 9 y diferencia 1
