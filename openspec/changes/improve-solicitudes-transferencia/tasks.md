# Tasks

## 1. Reproducir el congelamiento

- [ ] 1.1 Reproducir con el cliente (video/pasos, dispositivo y navegador) el congelamiento en Solicitudes y medir en DevTools (Performance) qué lo causa; verificar dejando la causa anotada en `design.md`

## 2. Backend

- [ ] 2.1 Validaciones al crear (origen≠destino, ítems no vacíos y sin duplicados, productos/locales del tenant, cantidades decimales > 0); verificar con tests de servicio
- [ ] 2.2 Finalizar con `inventario_movimientos.transferir(commit=False)` en una transacción (stock suficiente, bloqueo, usuario, referencia); verificar con tests: aprobación parcial, stock insuficiente sin cambios, rollback total
- [ ] 2.3 Recepción con movimientos `AJUSTE_RECEPCION` y creación de filas faltantes; verificar con tests de faltante, sobrante y re-recepción
- [ ] 2.4 Eliminar solo en PENDIENTE (409 en otro caso); verificar con test

## 3. Backoffice

- [ ] 3.1 Función `accionesPermitidas` y uso en tabla, tarjetas y modal (incluye admin; "Eliminar" solo en PENDIENTE); verificar en navegador con usuario admin, de origen y de destino
- [ ] 3.2 Cantidades con decimales en formulario y recepción; mostrar receptor y fecha de recepción en el detalle; verificar en navegador
- [ ] 3.3 Catálogo cargado una vez y sin imágenes, consulta de stock en lote con debounce, PDF sin bloquear; verificar con DevTools que al escribir no hay ráfagas de requests y que la pantalla no se congela

## 4. Verificación

- [ ] 4.1 Recorrer el flujo completo en local (crear → atender → finalizar → recibir con faltante) y verificar stock y movimientos en Historial
- [ ] 4.2 Ejecutar `openspec validate improve-solicitudes-transferencia --strict` y verificar que pasa

## Actualizar capacitación

- [ ] Actualizar `capacitacion/inventario/04-solicitudes-de-transferencia.html` (estados, acciones por local, recepción) y su fecha de "Última revisión"

## Workflow follow-up

- Archivar solo con OK del usuario, después de `fix-seguridad-inventario` y `fix-inventario-movimientos-trazabilidad`.
