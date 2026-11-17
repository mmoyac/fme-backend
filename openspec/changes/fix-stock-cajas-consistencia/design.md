## Context

`stock_cajas_proveedor` es un contador mantenido por eventos (enrolamiento, pedidos, preventa, ajuste) que no se recalcula desde `lotes`. Escrituras dispersas: `routers/enrolamiento.py:1035-1176`, `routers/pedidos.py` (131-310 confirmación, 394-508 cancelación, 1030-1117 creación), `routers/preventa.py` (296-362, 605-728, 1317-1348), `routers/stock_cajas.py:577-627` (ajuste). Movimientos en `movimientos_stock_cajas` (`cajas_movimiento`, `cajas_antes`, `cajas_despues`).

## Goals / Non-Goals

**Goals:** que el contador no se descuadre por los flujos conocidos, que cada cambio quede trazado con signo y antes/después, y poder detectar descuadres.

**Non-Goals:** reemplazar el contador por un cálculo en vivo desde `lotes` (cambio mayor; la reconciliación da visibilidad primero); unificar con la tabla `inventario`.

## Decisions

- **Servicio `services/stock_cajas_service.py`** con `mover_cajas(db, user, producto_id, proveedor_id, delta, tipo, referencia, notas)` que bloquea la fila (`FOR UPDATE`), valida no-negativo, actualiza disponibles/totales/fecha y registra el movimiento con signo y antes/después. Todos los flujos lo llaman.
  - *Alternativa*: parchar cada sitio — repite el bug en el próximo flujo.
- **Lotes disponibles**: filtro `reservado = False` y `proveedor_id` opcional.
- **Recepción por lote, no por categoría**: los lotes solo existen para productos de caja variable; quitar la comparación literal con "CARNES". Guard contra doble finalización (si ya estaba FINALIZADO no suma).
- **Reconciliación**: `GET /stock-cajas/reconciliacion` (solo lectura) con `count(lotes)` agrupado vs contador.
- **UI**: paginación con `skip/limit`, búsqueda, etiquetas para todos los tipos (`ENTRADA_ENROLAMIENTO`, `RESERVA_LOTE`, `VENTA_LOTE`, `DEVOLUCION_LOTE`, `LIBERACION_RESERVA`, `AJUSTE_INVENTARIO`), errores con `detail` del backend.

## Risks / Trade-offs

- [Quitar el filtro "CARNES" suma cajas de categorías que antes no sumaban] → la reconciliación lo hace visible; validar con el cliente qué productos usan lotes antes del deploy.
- [Pedidos que antes pasaban ahora se rechazan por falta de cajas] → mensaje claro con disponibles.
- [Descuadres existentes en producción] → ejecutar la reconciliación tras el deploy y ajustar con motivo "Reconciliación".

## Migration Plan

Sin migraciones. Deploy backend y luego backoffice; correr reconciliación y revisar diferencias con el cliente.
