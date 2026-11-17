# Tasks

## 1. Modelo y migración

- [x] 1.1 Agregar `solicitado_por_id`, `producido_por_id` (FK users, SET NULL) y relaciones a `OrdenProduccion`, y `motivo_diferencia` a `DetalleOrdenProduccion` en `database/models.py`; verificar que el módulo importa sin error
- [x] 1.2 Crear migración Alembic con las columnas + rol `produccion` por tenant (idempotente) + permiso al menú `/admin/produccion` si existe; verificar `alembic upgrade head` y `downgrade -1` en local, y que `SELECT tenant_id, nombre FROM roles WHERE nombre='produccion'` devuelve una fila por tenant
- [ ] 1.3 Agregar `produccion` a los roles por defecto al crear tenant en `routers/tenants.py` (alta de tenant); verificar creando un tenant de prueba en local — _implementado, falta verificación_

## 2. Validación de rol

- [x] 2.1 Crear `utils/permisos.py` con `ROLES_ADMIN`, `ROLES_PRODUCCION` y dependencia síncrona `require_roles(...)` (case-insensitive, 403); verificar con un script/llamada que un usuario sin rol válido recibe 403
- [x] 2.2 Aplicar `require_roles(ROLES_ADMIN)` a `POST /produccion/ordenes` y `DELETE /produccion/ordenes/{id}`; setear `solicitado_por_id = current_user.id` al crear; verificar con curl como admin (200) y como produccion (403)
- [x] 2.3 Aplicar `require_roles(ROLES_PRODUCCION)` a `POST /produccion/ordenes/{id}/finalizar`; setear `producido_por_id`; verificar con curl como produccion (200) y vendedor (403)
- [x] 2.4 En `routers/ordenes_trabajo.py`, si la OT es tipo `OP`, exigir rol admin antes de crear y setear `solicitado_por_id` en la OP; verificar que OT de servicio sigue funcionando para vendedor
- [ ] 2.5 En `routers/cotizaciones.py` setear `solicitado_por_id = current_user.id` en la OP automática (sin restricción de rol); verificar aceptando una cotización con faltante de stock — _implementado, falta verificación_

## 3. Cantidades reales y diferencia

- [x] 3.1 En `schemas/produccion.py`: `AjusteProduccion.cantidad_producida_real` con `ge=0` y `motivo_diferencia` opcional; `DetalleOrdenRead` con `motivo_diferencia` y `diferencia` calculada; `OrdenProduccionRead` con `solicitado_por` / `producido_por`; verificar que una cantidad negativa da 422
- [x] 3.2 En `finalizar_orden` persistir `motivo_diferencia` por detalle; verificar finalizando 3 de 4 con motivo y que `GET /produccion/ordenes` devuelve `diferencia = -1`, motivo y producido_por
- [x] 3.3 Confirmar que finalizar con menos no genera OP nueva y cierra la OT vinculada; verificar en BD tras el caso 3.2

## 4. Backoffice (fme-backoffice)

- [x] 4.1 Actualizar tipos y payload de finalización en `lib/api/produccion.ts` (motivo, diferencia, solicitado_por, producido_por); verificar `npm run build` sin errores de tipos
- [ ] 4.2 En `app/admin/produccion/page.tsx`: ocultar "Nueva OP" y "Eliminar" al rol `produccion`; en el modal de finalizar agregar motivo por detalle y mostrar diferencia (rojo si < 0); mostrar solicitado/producido por en la lista; verificar en navegador con usuario admin y usuario produccion — _implementado, falta verificación_
- [ ] 4.3 Ocultar creación de OT tipo OP en `app/admin/produccion/ordenes-trabajo/nueva/page.tsx` a roles no admin; verificar en navegador — _implementado, falta verificación_

## 5. Integración

- [x] 5.1 Flujo completo en local: admin crea OP de 4 cajas → usuario produccion la ve y finaliza con 3 + motivo → inventario +3, OP FINALIZADA, diferencia -1 visible al admin

## Workflow follow-up

- Antes del deploy, revisar nombres reales de roles admin en prod y avisar al cliente que vendedor/tesorero ya no podrán crear/finalizar OP.
- Archivar el change tras deploy y validación.
