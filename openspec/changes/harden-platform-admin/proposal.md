## Why

La consola de administración de plataforma (superadmin) y la gestión de tenants tienen brechas de seguridad que permiten a un usuario de un tenant afectar a otros:

- `/api/tenants` (listar, crear, editar, **eliminar** tenants y ver sus usuarios) solo exigía estar autenticado: cualquier usuario de cualquier tenant podía operarlo.
- Al "entrar" a un tenant, el superadmin recibía el `tenant_id` mutando su objeto ORM; un `commit` en la request podía persistir ese valor en su fila de `users`.
- El superadmin comparte tabla, login y token con los usuarios de tenant; puede autenticarse desde cualquier dominio, sin segundo factor, con tokens de 8 horas.
- No existe bitácora de las acciones de plataforma (alta, suspensión, entrada a un tenant).
- El aislamiento entre tenants depende de que cada consulta filtre `tenant_id` a mano (ya hubo fugas: `fix_cross_tenant_precios.py`, `check_tenant_isolacion.py`).
- Los permisos se derivan de nombres de menú ("Usuarios", "Mantenedores"): renombrar un menú cambia quién tiene acceso.

El proyecto EffiCoop (`D:\ProyectosAI\EffiCoop`, specs `platform/tenancy`, `platform/audit-trail`, `identity/authentication`, `identity/access-control`) ya resuelve estos puntos y se usa como referencia.

## What Changes

Por fases, cada una desplegable por separado:

1. **Contención inmediata** (hecho): `/api/tenants` exige superadmin; el contexto de tenant del superadmin ya no puede persistirse en la BD.
2. **Bitácora de plataforma**: tabla `audit_log` de solo inserción; se registran alta/edición/eliminación/activación de tenants, creación de superadmins y cada entrada/salida de un tenant.
3. **Acceso de soporte acotado**: el token de "entrar a tenant" dura 30 min, lleva `act_as` explícito y la UI muestra un banner permanente "Operando como <tenant>".
4. **Identidad de plataforma separada**: tabla `platform_admins` (fuera de `users`), TOTP obligatorio, login solo en el host de administración, tokens con `aud=platform` rechazados por la API de tenants y viceversa; bloqueo por intentos fallidos.
5. **Aislamiento en la BD (RLS)**: Postgres Row Level Security con `FORCE` en las tablas con `tenant_id`, fijando `app.tenant_id` por transacción (`set_config(..., true)`), tabla por tabla.
6. **Permisos `recurso:acción`**: catálogo global de permisos asignables a roles; el menú se deriva de los permisos y deja de ser la fuente de autorización.

## Capabilities

### New Capabilities
- `platform-admin`: administración de la plataforma multi-tenant (identidad del superadmin, gestión de tenants, acceso de soporte a un tenant, bitácora y aislamiento de datos).

### Modified Capabilities
<!-- Ninguna spec existente cubre autenticación ni tenants -->

## Impact

- **Backend**: `routers/auth.py`, `routers/superadmin.py`, `routers/tenants.py`, `routers/admin_users.py`, `database/database.py`, `database/models.py`, migraciones Alembic nuevas (audit_log, platform_admins, políticas RLS, permisos).
- **Backoffice**: `lib/auth.ts` (tokens separados de plataforma), `app/admin/superadmin`, `app/admin/tenants`, `app/admin/layout.tsx` (banner), `app/admin/mantenedores` (ocultar acceso a tenants a no-superadmins).
- **Operación**: crear los superadmins actuales en `platform_admins` y enrolar TOTP antes de desactivar `users.is_superadmin` (fase 4).
- **Riesgo**: la fase 5 (RLS) puede ocultar datos a código que hoy consulta sin contexto de tenant (jobs, webhooks, scripts); se activa tabla por tabla en dev antes de prod.
