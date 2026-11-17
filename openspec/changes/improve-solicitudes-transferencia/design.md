## Context

Ver `document-inventario-baseline/design.md` (Solicitudes) y el análisis del flujo: estados PENDIENTE/EN_PROCESO/FINALIZADO tomados de `estados_enrolamiento`; finalización en `routers/solicitudes_transferencia.py:279-307` sin validar stock; recepción en `:181-213` sin movimientos; UI en `components/solicitudes/`. El congelamiento reportado no está reproducido: la pantalla no renderiza imágenes, pero carga `GET /api/productos/?limit=1000` (con `imagen_url`) dos veces, pide stock por ítem en cada tecla y genera el PDF con html2canvas `scale:2` en el hilo principal.

## Goals / Non-Goals

**Goals:** reglas de negocio en el backend, trazabilidad completa en Historial, UI coherente con el backend y sin bloqueos.

**Non-Goals:** estados nuevos (cancelada/rechazada) ni tabla de estados propia — se evalúa en un change aparte si el cliente lo pide; integración con hojas de ruta.

## Decisions

- **Reutilizar `services/inventario_movimientos.transferir(..., commit=False)`** por ítem dentro de una transacción; si uno falla se hace rollback de todos. Valida stock y bloquea filas.
- **`AJUSTE_RECEPCION`** como nuevo `tipo_movimiento`: origen/destino según el signo de la diferencia, `referencia_id` = solicitud. Si falta la fila de inventario del destino, se crea (en vez de saltarse el ajuste).
- **Eliminar solo PENDIENTE**: después de EN_PROCESO hay compromisos del origen y, tras FINALIZADO, movimientos de stock; borrar dejaría el Historial huérfano.
- **Rendimiento**: endpoint liviano de productos para combos (id, nombre, sku, unidad; sin imagen) o reutilizar el existente con un parámetro `campos=basico`; hook compartido con cache en memoria; consulta de stock en lote (`GET /inventario/?local_id=X&producto_ids=...`) con debounce de 400 ms; PDF con `scale:1` y generado tras `requestIdleCallback`/import dinámico. Antes de optimizar se reproduce el congelamiento con el cliente (video o pasos) para confirmar la causa.
- **Permisos UI**: función única `accionesPermitidas(solicitud, usuario)` que replica las reglas del backend (incluye admin).

## Risks / Trade-offs

- [El congelamiento tiene otra causa (dispositivo, red)] → tarea explícita de reproducción antes de cerrar.
- [Finalizaciones antes permitidas ahora fallan por stock insuficiente] → el mensaje indica el producto; el origen ajusta la cantidad aprobada.

## Migration Plan

Sin migraciones (el tipo `AJUSTE_RECEPCION` es texto libre). Deploy backend y luego backoffice, después de `fix-seguridad-inventario` y `fix-inventario-movimientos-trazabilidad`.
