# Design

## Context

- Hay dos subsistemas de despacho (ver `openspec/specs/despacho/spec.md`): el **Sistema de Despachos** (`/api/despachos`, tabla `despachos`, picking) y las **Hojas de Ruta** (`/api/hojas-ruta`). El backoffice opera con Hojas de Ruta; el picking flow no tiene páginas propias.
- `GET /api/hojas-ruta/pedidos-disponibles` ya calcula "qué falta despachar": pedidos CONFIRMADO del tenant que no están en ningún `HojaRutaItem` y con `costo_delivery IS NOT NULL`, más solicitudes FINALIZADO con `requiere_delivery` sin hoja. Devuelve kg, total, pagado y dirección (del cliente).
- `GET /api/despachos/pendientes` usa la tabla `despachos` (otro criterio: sin despacho asignado). Un pedido metido en una hoja de ruta seguiría "pendiente" ahí.
- La tienda guarda `costo_delivery = 0` en los retiros (`services/tarifas_delivery.costo_delivery` → RETIRO = 0) y `modalidad_entrega` + `comuna_entrega` desde `add-delivery-por-comuna`. Los pedidos del backoffice fijan `modalidad_entrega` desde `requiere_delivery` (`add-modalidad-entrega-pedido`).
- El auto-confirmado tras el pago en línea (`services/pagos_online.autoconfirmar_pedido`) deja el pedido `es_pagado = True` y PENDIENTE cuando falla, y crea la alerta `pedido_pagado_sin_confirmar`.
- `/admin/despacho/tablero` ya muestra hojas del día y pedidos sin asignar; la spec lo marca como duplicado con Rutas.

## Goals / Non-Goals

**Goals:**
- Que al entrar a Despacho se vea de inmediato cuánto hay pendiente, dónde (comuna) y qué está trabado (pagado sin confirmar).
- Armar una hoja de ruta por comuna en pocos clics reutilizando el flujo actual.
- Una sola definición de "despachable" para la bandeja y para `pedidos-disponibles`.

**Non-Goals:**
- Mapa, geocodificación de pedidos, orden óptimo de la ruta.
- Cambiar el picking flow (`/api/despachos`) o consolidar el Tablero.
- Confirmar pedidos desde la bandeja (se enlaza al pedido; la confirmación sigue en Pedidos).

## Decisions

1. **Fuente de verdad = Hojas de Ruta.** "Por despachar" usa el criterio de `pedidos-disponibles` (no estar en ningún `HojaRutaItem`), no la tabla `despachos`, porque es el flujo que el negocio usa. Alternativa descartada: `/api/despachos/pendientes`, que ignora las hojas de ruta.
2. **Regla de elegibilidad compartida** en una función del router (ej. `_filtro_despachable(q)`): `estado = CONFIRMADO` y (`modalidad_entrega = 'DESPACHO'` o `costo_delivery > 0`). La usan la bandeja y `pedidos-disponibles`. Con esto un retiro web (RETIRO, costo 0) queda fuera y un delivery gratis (DESPACHO, costo 0) queda dentro.
3. **Endpoint `GET /api/hojas-ruta/bandeja`** (mismo router y permisos que `pedidos-disponibles`, mismo filtro por local para no admin) que devuelve:
   - `contadores`: `por_despachar`, `pagados_sin_confirmar`, `en_ruta`, `entregados_hoy`.
   - `pendientes`: lista con el mismo formato de `pedidos-disponibles` + `comuna` (`pedidos.comuna_entrega`; en solicitudes, `null`).
   - `pagados_sin_confirmar`: id, número, cliente, total, fecha.
   Un solo request para la portada. Los filtros (comuna, fechas, pagado) se aplican en el cliente: el volumen de pendientes es bajo (decenas) y así los chips muestran conteos sin más llamadas.
4. **"Pagados sin confirmar"** = pedidos del tenant en estado PENDIENTE con `es_pagado = True` y al menos un `PagoOnline` CONFIRMADO. Exigir el pago online evita mezclar pedidos del backoffice marcados pagados a mano que aún esperan confirmación por otros motivos.
5. **"Entregados hoy"** = `HojaRutaItem.entregado = True` con `fecha_entrega` en el día actual en zona `America/Santiago`. **"En ruta"** = hojas con estado `EN_RUTA`.
6. **Crear hoja con preselección**: la bandeja navega a `/admin/despacho/rutas?nueva=1&pedidos=1,2&solicitudes=5`; la página de Rutas abre el modal "Nueva Hoja de Ruta" y marca esos IDs si siguen disponibles. Se reutiliza todo el modal (chofer, vehículo, kg). Alternativa descartada: crear la hoja desde la bandeja con un modal nuevo (duplicaría validaciones).
7. **Portada**: contadores arriba, chips de comuna, filtros, tabla con checkbox (tarjetas en móvil con el `DataList` existente), y debajo las tarjetas de acceso actuales en una sección "Herramientas".

## Risks / Trade-offs

- [Pedidos antiguos del backoffice con delivery gratis (`costo 0`) y `modalidad_entrega = RETIRO` por defecto quedarían fuera] → verificar en prod antes de desplegar cuántos pedidos CONFIRMADO sin hoja tienen `costo_delivery = 0` y `RETIRO`; si los hay, revisarlos con el usuario.
- [La dirección viene de `clientes.direccion` (dato vivo, no snapshot del pedido)] → se mantiene como hoy; si el cliente cambia su dirección, la bandeja muestra la nueva. Snapshot por pedido queda para el change del mapa.
- [Filtrado en el cliente] → si un tenant llega a cientos de pendientes, mover filtros al endpoint.
- [Filtro por local para usuarios no admin] → los contadores siguen el mismo filtro que `pedidos-disponibles` para no mostrar números que el usuario no puede ver en la lista.

## Migration Plan

Sin migraciones. Desplegar backend y backoffice juntos (la portada nueva depende del endpoint). Rollback: revertir ambos; la regla de elegibilidad vuelve a `costo_delivery IS NOT NULL`.

## Open Questions

- Si los pedidos con `modalidad_entrega = DESPACHO` pero sin comuna (backoffice) deberían pedir la comuna al crearlos: queda para otro change.
