# Tasks

## 1. Verificación previa en prod

- [x] 1.1 Contar en prod los pedidos CONFIRMADO sin hoja de ruta con `costo_delivery = 0` y `modalidad_entrega = RETIRO` (quedarían fuera con la regla nueva); informar al usuario antes de desplegar — _prod 2026-11-19: 0 afectados (5 confirmados: 1 DESPACHO con costo, 4 RETIRO sin costo)_

## 2. Backend (`routers/hojas_ruta.py`)

- [x] 2.1 Función compartida de "pedido despachable" (CONFIRMADO, sin `HojaRutaItem`, `modalidad_entrega = 'DESPACHO'` o `costo_delivery > 0`) y usarla en `GET /pedidos-disponibles`; agregar `comuna` (`pedidos.comuna_entrega`) a su respuesta; verificar con un pedido RETIRO costo 0 (excluido) y uno DESPACHO costo 0 (incluido) en local
- [x] 2.2 `GET /api/hojas-ruta/bandeja` con `contadores` (`por_despachar`, `pagados_sin_confirmar`, `en_ruta`, `entregados_hoy` en `America/Santiago`), `pendientes` y `pagados_sin_confirmar`; mismo permiso y filtro por local que `pedidos-disponibles`; endpoint síncrono (`def`, no `async def`); verificar con curl en local
- [x] 2.3 Verificar aislamiento por tenant: un pedido despachable del tenant 2 no aparece en la bandeja del tenant 1

## 3. Backoffice

- [x] 3.1 Cliente API `obtenerBandejaDespacho()` y tipos; `npx tsc --noEmit` sin errores
- [x] 3.2 Portada `/admin/despacho`: contadores clicables, chips por comuna con conteo (incluye "Sin comuna"), filtros por fecha y pagado, lista con selección múltiple (tabla en escritorio, tarjetas en móvil) y enlace a cada pedido; tarjetas actuales en sección "Herramientas"; verificar en `localhost:3001` con datos de varias comunas
- [x] 3.3 "Pagados sin confirmar": lista con enlace al pedido para confirmarlo; verificar con un pedido pagado en línea cuyo tipo no tiene local por defecto
- [x] 3.4 Botón "Crear hoja de ruta con seleccionados" → `/admin/despacho/rutas?nueva=1&pedidos=…&solicitudes=…`; la página de Rutas abre el modal con esos IDs marcados (ignora los que ya no estén disponibles); verificar creando una hoja con los pedidos de una comuna y que salen de "Por despachar"
- [x] 3.5 Revisar en móvil (390 px) y escritorio que la portada no tenga scroll horizontal (`e2e/ancho.spec.ts` si aplica) — _revisado con capturas de Playwright en 1280 y 390 px; sin scroll horizontal_

## 4. Spec y cierre

- [ ] 4.1 Actualizar `openspec/specs/despacho/spec.md` al archivar: página índice (bandeja) y regla "Pedidos elegibles para Hoja de Ruta" con la modalidad de entrega
- [x] 4.2 Prueba del usuario en local antes de push — _OK del usuario 2026-11-19_

## Workflow follow-up

- No hay lecciones de capacitación del módulo Despacho; si se crean, incluir la bandeja.
- No hacer push ni archivar sin el OK del usuario.
