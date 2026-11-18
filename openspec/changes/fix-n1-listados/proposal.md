# Proposal

## Why

La medición en producción del 2026-11-18 mostró que `GET /api/productos/?limit=1000` tardaba entre 0,3 y 4,5 s (la pantalla de Producción, 6,5 s en total). La causa era el patrón N+1: el listado leía relaciones lazy dentro del bucle (stock e inventarios, unidad de medida) y hacía una consulta extra por producto. Al contar las consultas de todos los endpoints que usa el backoffice apareció el mismo patrón en pedidos, cobranza, clientes y en las estadísticas del dashboard. Además, el listado de clientes creaba registros de puntos dentro de un GET.

## What Changes

Solo cambia cómo se cargan los datos; las respuestas son las mismas (verificado comparando contra la versión anterior):

- `routers/productos.py` `listar_productos`: `joinedload(unidad_medida)` + `selectinload(inventarios)`.
- `routers/pedidos.py` `listar_pedidos`: despachos de todos los pedidos en una consulta (antes una por pedido) y `selectinload` en items/cheques/notas de crédito (con `joinedload` las colecciones multiplicaban las filas). Los ítems de cada pedido se devuelven ordenados por id (antes su orden no estaba definido).
- `routers/cobranza.py` `listar_cobranza`: relaciones del pedido (cliente, local, medio de pago, tipo de documento, estado, despacho, cheques, notas de crédito) cargadas en bloque en las dos consultas (cheques y transferencias).
- `routers/clientes.py` `listar_clientes`: puntos de todos los clientes en una consulta; sin registro = 0 puntos, igual que antes, pero ya **no se crea** el registro `PuntosCliente` dentro del GET.
- `routers/dashboard.py` `obtener_estadisticas_dashboard`: `selectinload(notas_credito)` en los pedidos sin pagar.

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
(ninguna: no cambian requisitos ni respuestas)

## Impact

- **fme-backend:** los cinco routers anteriores. Sin migraciones ni cambios de API.
- **fme-backoffice:** ninguno; las pantallas reciben los mismos datos más rápido.
- **Capacitación:** no aplica (sin cambios de comportamiento ni pantallas).
