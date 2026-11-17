# Design

## Context

- Stock por local vive en `inventario` (`producto_id`, `local_id`, `cantidad_stock` Numeric(10,3)), único por producto/local.
- El historial está en `movimientos_inventario` (`tipo_movimiento` string libre: TRANSFERENCIA, AJUSTE, PEDIDO, MERMA…; `usuario` es texto, sin FK; `referencia_id` genérico).
- `POST /inventario/ajuste-merma` es el precedente más cercano: valida tenant, ajusta stock y registra movimiento con el nombre del usuario.
- Backoffice: `/admin/inventario/page.tsx` con pestañas `ExistenciasTab`, `TransferenciasTab`, `HistorialTab`.
- Regla del proyecto (incidente 2026-11-11): endpoints con BD síncrona MUST ser `def`, nunca `async def`.
- No hay exportación Excel en el backend (no está `openpyxl`).

## Goals / Non-Goals

**Goals:**
- Documento de conteo con líneas, estados y auditoría completa por línea y por conteo.
- Finalización atómica que ajusta stock y deja movimientos trazables al conteo.
- Captura cómoda desde tablet/celular en el backoffice (PWA).

**Non-Goals:**
- Productos con lotes / caja variable (stock gestionado en Stock Cajas).
- Valorización ($) del conteo — queda para `add-valorizacion-inventario`.
- Captura offline, escaneo con cámara, conteo ciego (ocultar stock del sistema) y aprobación por supervisor — posibles mejoras futuras.

## Decisions

### D1. Modelo: cabecera + líneas
- `conteos_inventario`: `id`, `tenant_id`, `local_id`, `tipo` (COMPLETO|PARCIAL), `estado` (EN_PROCESO|FINALIZADO|CANCELADO), `observacion`, `usuario_creador_id`, `fecha_inicio`, `usuario_cierre_id`, `fecha_cierre`.
- `conteo_inventario_items`: `id`, `conteo_id` (CASCADE), `producto_id`, `stock_sistema` Numeric(10,3) null, `cantidad_contada` Numeric(10,3) null, `diferencia` Numeric(10,3) null, `ajuste_aplicado` Numeric(10,3) null, `usuario_captura_id`, `fecha_captura`. Unique (`conteo_id`, `producto_id`).
- Un conteo abierto por local: índice único parcial `(local_id) WHERE estado = 'EN_PROCESO'` en PostgreSQL + validación en el endpoint (409).
- *Alternativa descartada*: solo movimientos `AJUSTE_CONTEO` sin tabla propia — no permite conteo en curso, ni líneas sin diferencia, ni reporte "sistema vs contado".

### D2. Ajuste por diferencia, no sobrescritura
Al finalizar se aplica `stock_actual += diferencia` (diferencia calculada al capturar), en vez de `stock = contado`. Así las ventas/transferencias que ocurren entre la captura de una línea y la finalización no se pierden. Si el usuario corrige una línea, se recaptura `stock_sistema` del momento.
- *Alternativa*: sobrescribir con `contado` — más simple, pero borra ventas ocurridas durante un conteo largo con el local abierto.

### D3. Auditoría con FK a usuario
Se guardan `usuario_*_id` (FK `users.id`, RESTRICT) en cabecera y líneas. En `movimientos_inventario` se agrega `usuario_id` nullable (FK `ON DELETE SET NULL`, para no bloquear el borrado de usuarios por el historial) (además del texto `usuario` existente, que se sigue llenando) y se usa `tipo_movimiento='AJUSTE_CONTEO'`, `referencia_id=conteo_id`. Diferencia positiva → `local_destino_id = local`; negativa → `local_origen_id = local`, cantidad en valor absoluto (consistente con MERMA/TRANSFERENCIA).

### D4. Transacción y concurrencia al finalizar
Finalizar se ejecuta en una transacción: `SELECT ... FOR UPDATE` sobre el conteo (evita doble finalización) y sobre las filas de `inventario` afectadas; si no existe fila de inventario para un producto con diferencia positiva, se crea. Cualquier error → rollback completo. Si el stock resultante quedara negativo, se trunca a 0 (igual que pedidos y merma, que nunca dejan stock negativo); `ajuste_aplicado` guarda el ajuste real y la nota del movimiento lo indica.

### D5. API (`routers/conteos_inventario.py`, prefijo `/conteos-inventario`)
- `POST /` iniciar · `GET /` listar (filtros) · `GET /{id}` detalle
- `POST /{id}/items` agregar productos (`producto_ids` o `categoria_id`)
- `DELETE /{id}/items/{item_id}` quitar línea (solo parcial, solo EN_PROCESO)
- `PUT /{id}/items/{item_id}` registrar `cantidad_contada`
- `POST /{id}/finalizar` · `POST /{id}/cancelar`
- `GET /{id}/excel` → `StreamingResponse` xlsx (openpyxl)
Lógica en `services/conteo_inventario_service.py`; todos los endpoints `def` síncronos con `get_current_active_user` y filtro por `tenant_id`.

### D6. Backoffice
Nueva pestaña **Conteo** en `/admin/inventario`: lista de conteos + botón "Nuevo conteo" (local, tipo). Pantalla de captura con buscador, filtro por categoría, input numérico grande por línea con guardado al salir del campo, indicador contadas/total y resaltado de diferencias. Botón Finalizar con resumen de diferencias y confirmación. Botón Exportar Excel en el detalle. `HistorialTab` muestra `AJUSTE_CONTEO` con link al conteo.

## Risks / Trade-offs

- [Conteo completo con muchos productos lento en la UI] → paginación/virtualización y guardado por línea (no un submit gigante).
- [Usuario olvida finalizar y el conteo queda abierto bloqueando el local] → lista muestra conteos abiertos con antigüedad; se puede cancelar.
- [Corrección de línea recaptura stock_sistema y puede confundir] → el detalle muestra fecha y usuario de la última captura.
- [Nueva dependencia openpyxl] → liviana, pura Python; reutilizable para el resto de exportaciones pedidas por el cliente.

## Migration Plan

1. Migración Alembic: crear tablas, índice parcial y columna `movimientos_inventario.usuario_id` (nullable, sin backfill).
2. Agregar `openpyxl` a `requirements.txt`.
3. Deploy backend (push a main; migraciones vía entrypoint) y luego backoffice.
4. Asignar el menú/pestaña a los roles que correspondan.
Rollback: revertir deploy; la migración `downgrade` elimina tablas y columna (los ajustes ya aplicados quedan en stock y en movimientos).

## Open Questions

- ¿Qué roles ven la pestaña Conteo? Se resuelve con la configuración de menús existente.
