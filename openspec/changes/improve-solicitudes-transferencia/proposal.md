## Why

Solicitudes es el flujo con el que las tiendas se abastecen entre sí y el cliente reportó que la pantalla "se congela" (minuta 2026-11-16, Fiabilidad). Además el backend no valida stock (puede dejar el origen en negativo), los ajustes de recepción no quedan en el Historial, eliminar no revierte nada y la UI muestra acciones que el backend rechaza. Ver brechas en `document-inventario-baseline/design.md`. Requiere que `fix-seguridad-inventario` ya esté aplicado.

## What Changes

- **Validaciones al crear**: origen ≠ destino, al menos un producto, sin productos repetidos, productos y locales del tenant, cantidades > 0 con hasta 3 decimales.
- **Finalizar** usa el servicio común de movimientos (`fix-inventario-movimientos-trazabilidad`): valida stock suficiente, bloquea filas, registra usuario real y `referencia_id`, sin stock negativo.
- **Recepción** registra cada diferencia como movimiento `AJUSTE_RECEPCION` (visible en Historial) y nunca descuadra si falta la fila de inventario.
- **Eliminar** solo en `PENDIENTE` (antes de que el origen la atienda); después se gestiona con la recepción.
- **UI**: permisos de botones iguales a los del backend (incluye admin), "Eliminar" solo cuando corresponde, cantidades con decimales.
- **Fluidez**: catálogo de productos cargado una vez y sin imágenes, consulta de stock con debounce y en lote, PDF generado sin bloquear la pantalla. Se reproduce primero el congelamiento reportado.

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-solicitudes-transferencia`: cambian "Crear solicitud entre locales" (validaciones, decimales), "Finalizar mueve stock" (stock suficiente, usuario) y "Registrar recepción" (movimientos); se agregan "Eliminación solo en estado pendiente" y "Pantalla de solicitudes fluida".

## Impact

- Backend: `routers/solicitudes_transferencia.py`, `schemas/solicitud_transferencia.py` (cantidades decimales), uso de `services/inventario_movimientos.py`.
- Backoffice: `components/solicitudes/SolicitudesTable.tsx`, `SolicitudForm.tsx`, `SolicitudDetalleModal.tsx`, hooks de productos/stock, `generarPDFSolicitudHTML.ts`.
- Depende de `fix-seguridad-inventario` y `fix-inventario-movimientos-trazabilidad`. Sin migraciones.
