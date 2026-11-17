# Design

## Context

- `pedidos` hoy tiene `local_despacho_id` y `costo_delivery`, pero no la modalidad. `requiere_delivery` existe en los requests (`PedidoBackofficeCreate` en `schemas/pedido.py` y `AceptarCotizacionRequest` en `routers/cotizaciones.py`), pero no se guarda.
- Hay tres caminos a ENTREGADO: POS directo (`routers/pedidos.py`, `es_pedido_pos_directo`), hoja de ruta (`POST /hojas-ruta/{hoja}/items/{item}/entregar`, que ya guarda `fecha_entrega` y `notas_entrega` en `HojaRutaItem`) y despacho (`PUT /despachos/{id}` con estado ENTREGADO). El retiro hoy es un cambio manual de estado (`PUT /pedidos/{id}`).
- Cobranza (`routers/cobranza.py`) ya calcula `entregado` a partir del despacho o del estado final.

## Goals / Non-Goals

**Goals:** modalidad explícita y persistida; registro de quién y cuándo en las dos modalidades; datos de quién retiró; filtros para monitorear retiros pendientes; visibilidad en Cobranza.

**Non-Goals:** firma digital o foto de la entrega; notificar al cliente que su pedido está listo para retirar (puede ser un change posterior vía n8n); cambiar el flujo de hojas de ruta; entregas parciales.

## Decisions

1. **Columnas en `pedidos`, no una tabla nueva.** Hay una sola entrega por pedido (no hay entregas parciales), así que basta con: `modalidad_entrega VARCHAR(10) NOT NULL DEFAULT 'RETIRO'`, `fecha_entrega TIMESTAMPTZ NULL`, `entregado_por_id FK users SET NULL`, `retirado_por_nombre VARCHAR(120)`, `retirado_por_rut VARCHAR(12)` y `nota_entrega TEXT`.
2. **Helper único `services/entrega_pedido.py` → `registrar_entrega(db, pedido, usuario, ...)`.** Lo usan el retiro, la hoja de ruta, el despacho y el POS. Pone ENTREGADO, `fecha_entrega` y `entregado_por_id`, y es idempotente: si el pedido ya está entregado, no pisa la fecha.
3. **Compatibilidad del request.** Se acepta `modalidad_entrega` explícita y, si no viene, se deriva de `requiere_delivery`. Los clientes actuales siguen funcionando sin cambios.
4. **El retiro exige CONFIRMADO o EN_PREPARACION.** Un pedido PENDIENTE esperando producción (como el #00127) no se puede retirar todavía, lo que evita entregar algo sin stock descontado.
5. **El cambio manual de estado a ENTREGADO por `PUT /pedidos/{id}` se mantiene** por compatibilidad, pero también pasa por `registrar_entrega` para no perder quién ni cuándo.
6. **Endpoints sincrónicos** (`def`), por el incidente del event loop.

## Risks / Trade-offs

- **Backfill aproximado:** los retiros históricos quedan sin quién ni cuándo exactos. Se acepta: solo se copian las fechas que se conocen.
- **Pedidos POS no directos:** si se crean sin delivery, quedan como RETIRO aunque no lo sean. Es el comportamiento razonable por defecto y se puede cambiar en el detalle.

## Migration Plan

Una revisión Alembic que agrega las columnas y hace el backfill: primero DESPACHO para los pedidos con `costo_delivery`, despacho o ítem de hoja de ruta; luego copia `fecha_entrega` desde `hoja_ruta_items.fecha_entrega` o desde el despacho entregado. El downgrade elimina las columnas.
