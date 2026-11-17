## 1. Contención inmediata

- [x] 1.1 Proteger todos los endpoints de `routers/tenants.py` con `get_current_superadmin` (antes: cualquier usuario autenticado)
- [x] 1.2 Reemplazar `user.tenant_id = tenant_id` en `routers/auth.py` (2 lugares) por `_aplicar_contexto_tenant` (`set_committed_value` + listener `refresh`); verificado que el valor no se persiste tras un commit
- [ ] 1.3 Backoffice: ocultar la pestaña "Tenants" de `app/admin/mantenedores` y la ruta `/admin/tenants` a usuarios sin `is_superadmin`
- [ ] 1.4 Revisar en BD de prod que ningún superadmin tenga `tenant_id` alterado por el bug anterior
- [ ] 1.5 Unificar `/api/tenants` y `/api/superadmin` (hoy duplican listado y activación de tenants)

## 1b. Acceso por host

- [ ] 1b.1 Reemplazar la confianza en `X-Forwarded-Host` enviado por el cliente: OJO, la landing llama a la API compartida y manda su hostname en ese header (así se resuelve el tenant hoy). Forzarlo en nginx rompería la tienda; usar el header `Origin` (validado contra dominios registrados) o un host de API por tenant
- [ ] 1b.2 Claim `aud` + `tid` en los tokens; validar `tid` contra el tenant del host en cada request
- [ ] 1b.3 Login del POS con código de tenant; eliminar el fallback "solo por email" de `routers/auth.py`
- [ ] 1b.4 DNS/nginx: `effichain-admin`, `effichain-<slug>` (tienda) y `effichain-<slug>-admin` (backoffice) bajo `effi4tech.cl` con el comodín existente; slugs `admin` y `*-admin` reservados
- [ ] 1b.5 Resolver tenant por host: patrón `effichain-<slug>[-admin]` o `dominio_principal` (con `admin.`/`www.`)
- [ ] 1b.6 Migrar El Olivo y demás tenants de `*.lexastech.cl` a `effichain-<slug>`; mantener redirección 301 desde los hosts antiguos
- [ ] 1b.7 Backoffice: detección de espacio por hostname (plataforma vs tenant) con rutas separadas

## 2. Bitácora de plataforma

- [ ] 2.1 Migración `audit_log` (solo INSERT/SELECT para el rol de la app)
- [ ] 2.2 Helper `registrar_auditoria(db, accion, ...)` en la misma transacción
- [ ] 2.3 Registrar: CRUD de tenants, toggle activo, crear superadmin, switch/exit tenant, login exitoso/fallido de superadmin
- [ ] 2.4 Endpoint y pantalla de consulta de bitácora (plataforma y por tenant)

## 3. Acceso de soporte acotado

- [ ] 3.1 Token de switch-tenant con TTL 30 min y claim `act_as`
- [ ] 3.2 Banner permanente "Operando como <tenant>" en `app/admin/layout.tsx` con botón salir
- [ ] 3.3 Rechazar el token de switch-tenant para `create-superadmin` y endpoints de plataforma

## 4. Identidad de plataforma separada

- [ ] 4.1 Migración `platform_admins` + traspaso de los superadmins actuales
- [ ] 4.2 Claim `aud` en todos los tokens; `get_current_user` rechaza `aud=platform`
- [ ] 4.3 Login de plataforma solo en el host de administración, con TOTP obligatorio
- [ ] 4.4 Bloqueo temporal por intentos fallidos y reducción de TTL de tokens de plataforma
- [ ] 4.5 Eliminar `users.is_superadmin` una vez migrado

## 5. Aislamiento por RLS

- [ ] 5.1 Rol de BD `fme_app` sin `BYPASSRLS` ni ownership; `DATABASE_URL` de la app apunta a él
- [ ] 5.2 Listener `after_begin` que fija `app.tenant_id` según el usuario/contexto de la request
- [ ] 5.3 Helper de migración `enable_tenant_rls(table)` / `disable_tenant_rls(table)`
- [ ] 5.4 Fijar tenant explícito en jobs, webhooks de pago y endpoints usados por n8n
- [ ] 5.5 Activar RLS tabla por tabla (empezar por clientes, pedidos, precios) con prueba de "consulta sin filtro solo ve su tenant"

## 6. Permisos `recurso:acción`

- [ ] 6.1 Catálogo de permisos y tabla rol↔permiso; roles iniciales al crear tenant
- [ ] 6.2 Dependencia `require_permission("users:write")` y reemplazo de `get_current_admin_user`
- [ ] 6.3 Menú derivado de permisos; regla que impide quitar el último administrador del tenant
