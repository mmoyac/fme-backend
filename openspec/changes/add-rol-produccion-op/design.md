# Design

## Context

- Roles: tabla `roles` scoped por tenant; RBAC solo de menú (`role_menu_permissions`). Ningún endpoint de producción revisa `current_user.role`.
- OP se crea en 3 lugares: `routers/produccion.py` (`POST /ordenes`), `routers/ordenes_trabajo.py` (crear OT tipo OP, ~L346) y `routers/cotizaciones.py` (aceptar cotización, ~L510).
- `POST /produccion/ordenes/{id}/finalizar` ya recibe `ConfirmacionFinalizacion.detalles_ajustes[{detalle_id, cantidad_producida_real}]`, guarda `detalle.cantidad_producida`, mueve inventario y cierra la OT vinculada. La OP ya se cierra con lo real: el comportamiento de "sin saldo" existe, solo se formaliza.
- Nombres de rol admin en uso: `admin` (auth bootstrap), `administrador` (seed), `superadmin` (plataforma).

## Goals / Non-Goals

**Goals:**
- Validación de rol en backend para crear / finalizar / eliminar OP.
- Persistir solicitante, productor y motivo por detalle.

**Non-Goals:**
- RBAC genérico por endpoint para el resto del sistema.
- Cambiar el cálculo de consumo de insumos al finalizar.
- Saldos pendientes u OP complementarias.

## Decisions

1. **Helper `require_roles(*nombres)`** como dependencia FastAPI en `utils/permisos.py` (nuevo), que compara `current_user.role.nombre` en minúsculas contra el set dado y lanza 403. Constantes `ROLES_ADMIN = {"admin","administrador","superadmin"}` y `ROLES_PRODUCCION = ROLES_ADMIN | {"produccion"}`.
   - Debe ser `def` síncrono (regla del incidente de event loop: nada `async def` que toque BD síncrona). Alternativa descartada: permiso por menú (`/admin/produccion`) — no distingue crear de finalizar.
   - En `ordenes_trabajo.py` la validación se hace dentro de la función solo cuando `tipo_ot.codigo == "OP"`, no como dependencia, porque las OT de servicio no se restringen.
2. **Columnas nuevas** (migración Alembic):
   - `ordenes_produccion.solicitado_por_id` y `producido_por_id`: `Integer FK users.id ON DELETE SET NULL`, nullable (OP históricas quedan NULL).
   - `detalles_orden_produccion.motivo_diferencia`: `Text` nullable.
   - Alternativa descartada: usar `notas` de la OP para el motivo — no es por detalle ni consultable.
3. **Rol `produccion` por migración de datos**: para cada tenant, `INSERT` del rol si no existe (respeta `uq_role_tenant_nombre`) y del permiso al `menu_items.href = '/admin/produccion'` si ese menú existe. Para tenants creados después, agregar `produccion` a la creación de roles por defecto en el alta de tenant (`routers/superadmin.py`).
4. **Diferencia calculada, no persistida**: `diferencia` es propiedad/computed field en `DetalleOrdenRead` (`cantidad_producida - cantidad_programada` o `None`). Evita inconsistencias.
5. **Schemas**: `AjusteProduccion` agrega `motivo_diferencia: Optional[str]` y valida `cantidad_producida_real >= 0` (`Field(ge=0)`). `OrdenProduccionRead` agrega `solicitado_por` / `producido_por` como `{id, nombre, email}` opcional.
6. **Backoffice**: `app/admin/produccion/page.tsx` lee el rol del usuario (ya disponible en sesión) para ocultar "Nueva OP" y "Eliminar" al rol `produccion`; el modal de finalizar agrega campo motivo por detalle y muestra diferencia en rojo cuando < 0. Ocultar es solo UX: la seguridad está en el backend.

## Risks / Trade-offs

- [Usuarios vendedor/tesorero que hoy crean OP pierden acceso] → avisar al cliente antes del deploy; el admin puede reasignar roles.
- [Tenants con rol admin con otro nombre (ej. "Administrador" con mayúscula)] → comparación case-insensitive; revisar nombres reales en prod antes de desplegar.
- [Menú `/admin/produccion` no existe en algún tenant] → la migración omite el permiso sin fallar.

## Migration Plan

1. Revisar en prod `SELECT tenant_id, nombre FROM roles` para confirmar nombres de rol admin.
2. Deploy normal (push a main; migraciones automáticas por entrypoint).
3. Admin de cada tenant asigna rol `produccion` a usuarios de cocina.
4. Rollback: `alembic downgrade` elimina columnas; el rol `produccion` se puede dejar (inocuo) o borrar en el downgrade si no tiene usuarios.
