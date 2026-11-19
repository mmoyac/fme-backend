# Proposal

## Why

Desde una OP finalizada se pueden imprimir las etiquetas nutricionales (botón 🏷️, change `add-etiquetas-desde-produccion` del backoffice), pero el sistema no deja registro. Con muchas OP finalizadas no hay forma de saber a cuáles ya se les imprimieron etiquetas y a cuáles no.

## What Changes

- La OP registra si sus etiquetas fueron impresas: `ordenes_produccion.etiquetas_impresas_at` y `etiquetas_impresas_por_id` (FK `users`, SET NULL).
- La marca es **manual**: el usuario confirma "Marcar como impresas" en el modal de etiquetas después de verificar que salieron bien. Generar/imprimir el PDF NO marca la OP.
- `POST /produccion/ordenes/{id}/etiquetas-impresas` marca (solo OP `FINALIZADA`; rol producción o admin).
- `DELETE /produccion/ordenes/{id}/etiquetas-impresas` desmarca (solo admin), para corregir errores.
- `GET /produccion/ordenes` incluye `etiquetas_impresas_at` y `etiquetas_impresas_por`.
- Backoffice: badge "Etiquetas pendientes / impresas" en OP finalizadas, filtro "Etiquetas" en la lista de Producción y aviso en el modal si ya se imprimieron.

## Impact

- Backend: `database/models.py`, `schemas/produccion.py`, `routers/produccion.py`, migración Alembic.
- Backoffice: `lib/api/produccion.ts`, `app/admin/produccion/page.tsx`, `components/produccion/EtiquetasOrdenModal.tsx`.
- Sin capacitación existente del módulo Producción que actualizar.
