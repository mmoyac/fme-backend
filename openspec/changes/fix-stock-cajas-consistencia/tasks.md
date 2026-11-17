# Tasks

## 1. Servicio de cajas

- [ ] 1.1 Crear `services/stock_cajas_service.mover_cajas` (bloqueo, no-negativo, totales, fecha, movimiento con signo y antes/después); verificar con tests de servicio contra PostgreSQL

## 2. Flujos

- [ ] 2.1 Recepción: usar el servicio, contar todos los lotes del enrolamiento y no sumar dos veces; verificar con tests
- [ ] 2.2 Pedidos CAJAS_VARIABLES (crear, confirmar, cancelar) y preventa (crear, quitar ítem, cancelar, picking) usan el servicio y rechazan sin cajas suficientes; verificar con tests de cada flujo
- [ ] 2.3 `/lotes-disponibles` excluye reservados y acepta `proveedor_id`; verificar con test
- [ ] 2.4 Ajuste manual: entero ≥ 0, motivo obligatorio, vía servicio; verificar por API (−1 → 400, ajuste válido registra motivo y antes/después)
- [ ] 2.5 `GET /stock-cajas/reconciliacion`; verificar con test de un par descuadrado

## 3. Backoffice

- [ ] 3.1 Resumen con etiquetas correctas, Stock Detallado con búsqueda y paginación, Movimientos paginados con etiquetas y signo, ajuste con motivo y errores visibles; verificar en navegador

## 4. Verificación

- [ ] 4.1 Ejecutar la reconciliación en la BD local antes y después y verificar que los flujos de prueba no generan diferencias
- [ ] 4.2 Ejecutar `openspec validate fix-stock-cajas-consistencia --strict` y verificar que pasa

## Workflow follow-up

- Archivar solo con OK del usuario, después de `document-inventario-baseline` y `fix-seguridad-inventario`.
