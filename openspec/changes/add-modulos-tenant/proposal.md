## Why

EffiChain no tiene el concepto de módulo contratado: los 21 ítems de menú son globales, el admin de cada tenant puede asignarse cualquiera desde Roles y permisos, y el backend no bloquea ninguna API por módulo. No hay forma de vender planes distintos ni de impedir que un tenant use lo que no contrató. EffiCoop (`platform/tenancy/modules.py`, `require_module`) ya resuelve esto y se replica aquí.

## What Changes

- Catálogo fijo de módulos en código: **núcleo** (siempre disponible) + **12 módulos contratables** con dependencias entre ellos.
- Registro de los módulos contratados por cada tenant, administrado solo desde la consola de plataforma, con validación de dependencias y registro de cada cambio.
- Cada API de un módulo rechaza con HTTP 403 (`modulo_no_contratado`) las requests de tenants que no lo tienen, incluidas las públicas de la tienda online.
- Cada ítem de menú pertenece a un módulo: el menú del usuario solo muestra módulos contratados y el admin del tenant solo puede asignar a sus roles menús de módulos contratados.
- **BREAKING (controlado)**: un tenant pierde acceso a lo no contratado. La migración asigna todos los módulos a los tenants existentes, por lo que nadie pierde acceso al desplegar.

## Capabilities

### New Capabilities
- `modulos-tenant`: catálogo de módulos, contratación por tenant, bloqueo de APIs y menús según los módulos contratados.

### Modified Capabilities
<!-- Ninguna spec existente cubre menús ni permisos por tenant -->

## Impact

- **Backend**: nuevo `utils/modulos.py` (catálogo + dependencia), migración Alembic (`tenant_modulos`, `menu_items.modulo`), `routers/superadmin.py` (endpoints de módulos), `routers/auth.py` (`/menu`), `routers/admin_users.py` (asignación de menús), `main.py` (dependencia de módulo por router), `/api/auth/users/me` (lista de módulos del tenant).
- **Backoffice**: consola de plataforma (casillas de módulos por tenant), pestañas de Mantenedores filtradas por módulo, manejo del 403 `modulo_no_contratado`.
- **Landing**: la tienda de un tenant sin "Tienda online" responde 403; debe mostrar un mensaje en lugar de romperse.
- **Relación**: usa la consola y la bitácora del change `harden-platform-admin`; si la bitácora aún no existe, el registro de cambios queda como tarea pendiente enlazada.
