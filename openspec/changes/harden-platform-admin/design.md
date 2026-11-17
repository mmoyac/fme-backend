## Context

Backend FastAPI + SQLAlchemy **síncrono** sobre Postgres, una sola BD con columna `tenant_id` (~20 tablas). Tenant resuelto por hostname en el login; el JWT lleva `tenant_id`. Superadmin = `users.is_superadmin`. Deploy = push a `main` (migraciones automáticas en el entrypoint).

## Goals / Non-Goals

**Goals:** que ningún usuario de tenant pueda operar sobre otro tenant ni sobre la plataforma; que todo acceso de plataforma quede auditado; que el aislamiento no dependa de que cada consulta recuerde filtrar.

**Non-Goals:** migrar a BD por tenant; proveedor externo de identidad (Auth0/Clerk/Keycloak); reescribir a async.

## Decisions

### D1. Contexto de tenant del superadmin sin mutar la fila
`set_committed_value(user, "tenant_id", t)` asigna sin marcar el atributo como modificado, de modo que ningún flush lo escribe. Se guarda además en un atributo no mapeado (`_ctx_tenant_id`) y un listener `refresh` de `User` lo reaplica cuando la sesión recarga el objeto tras un commit (`expire_on_commit=True`). Alternativas descartadas: `expunge` (rompe lazy loads de `role.menus`) y un objeto contexto separado (exige tocar todos los routers que leen `current_user.tenant_id`).

### D2. RLS con `set_config` local a la transacción
Como EffiCoop (`core/db.py`, `core/migration_helpers.py`): `ENABLE` + `FORCE ROW LEVEL SECURITY` y política `tenant_id = current_setting('app.tenant_id', true)::int`. En SQLAlchemy síncrono se fija con un listener `Session.after_begin` que ejecuta `SELECT set_config('app.tenant_id', :t, true)`; es local a la transacción y seguro con pool. Sin contexto, la consulta devuelve 0 filas. La app debe conectarse con un rol **no dueño** de las tablas y sin `BYPASSRLS` (el superusuario siempre ignora RLS). Procesos sin request (jobs, webhooks MP, n8n) fijan el tenant explícitamente. Todo en `def` síncronos, nunca `async def` con la BD síncrona (incidente 2026-11-11).

### D3. Identidad de plataforma separada
Tabla `platform_admins` + claim `aud` (`platform` | `tenant`). `get_current_user` rechaza `aud=platform`; `get_current_platform_admin` solo acepta `aud=platform` y host de administración. TOTP con `pyotp`. Se mantiene "entrar a tenant" como token `aud=tenant` con `act_as=<admin_id>`, TTL 30 min, auditado.

### D4. Bitácora en la misma transacción
`audit_log` (actor, tipo de actor, tenant afectado, acción, recurso, detalle JSON, IP, request id, fecha) se inserta en la misma transacción que el cambio. El rol de la app solo tiene `INSERT`/`SELECT` sobre ella (sin `UPDATE`/`DELETE`).

### D5. Acceso por host (mismo esquema que EffiCoop)
El host determina el espacio; cada token solo es válido en su espacio. Convención de EffiCoop en prod: `BASE_DOMAIN=effi4tech.cl`, prefijo `efficoop-`, consola `efficoop-admin.effi4tech.cl`, certificado comodín `*.effi4tech.cl`. Para fme se usa prefijo `effichain-` (producto EffiChain):

Hay dos tipos de tenant: **con dominio propio** (p. ej. Masas Estación, `masasestacion.cl`) y **sin dominio** (p. ej. El Olivo), que usa el dominio de la empresa. Todo tenant tiene siempre sus hosts `effichain-*`; el dominio propio es un alias opcional.

| Espacio | Tenant sin dominio (El Olivo) | Tenant con dominio (Masas Estación) | Quién | Token |
|---|---|---|---|---|
| Consola de plataforma | `effichain-admin.effi4tech.cl` | (mismo) | `platform_admins` + TOTP | `aud=platform`, TTL corto |
| Tienda pública | `effichain-elolivo.effi4tech.cl` | `masasestacion.cl` / `www.` (alias de `effichain-masasestacion.effi4tech.cl`) | clientes | — |
| Backoffice | `effichain-elolivo-admin.effi4tech.cl` | `admin.masasestacion.cl` (alias de `effichain-masasestacion-admin.effi4tech.cl`) | usuarios del tenant | `aud=tenant`, `tid` |
| POS / móvil | API + código de tenant en el login | (igual) | usuarios del tenant | `aud=pos`, `tid` |

- Se usa `-admin` como sufijo (no `admin.effichain-<slug>…`) para quedar en un solo nivel y que el comodín `*.effi4tech.cl` cubra todos los hosts sin certificados por tenant. Los dominios propios sí requieren su certificado (Let's Encrypt por dominio, como hoy).
- Resolución del tenant desde el host: (1) `effichain-<slug>[-admin].effi4tech.cl` → por `codigo`/slug; (2) `[admin.|www.]<dominio>` → por `dominio_principal`. El sufijo `-admin` o prefijo `admin.` indica el espacio backoffice.
- El slug `admin` y cualquier slug terminado en `-admin` quedan reservados.
- En cada request de tenant el backend compara `tid` del token con el tenant resuelto desde el host; si difieren → 401.
- Las rutas `/api/platform/*` solo responden con host `effichain-admin.effi4tech.cl` y `aud=platform`.
- nginx fija `X-Forwarded-Host` desde `$host`; el backend no confía en el valor que envíe el cliente. Opcional: lista de IPs permitidas para `effichain-admin`.
- El backoffice Next.js detecta el espacio por hostname (como `realmForHost` de EffiCoop) y sirve un árbol de rutas distinto; un solo deploy.
- Se elimina el login "solo por email" para IP/localhost; el POS envía el código de tenant.

### D6. Acceso de soporte con ticket
En la consola: "Entrar a <tenant>" + motivo obligatorio → ticket de un solo uso (60 s) → redirección a `effichain-<slug>-admin.effi4tech.cl/soporte?ticket=…` → se canjea por token `aud=tenant`, `tid`, `act_as=<admin>`, TTL 30 min. Banner permanente en la UI. Entrada, cambios y salida se auditan en la bitácora de plataforma y en la del tenant. Reemplaza `switch-tenant` (que guarda el token de superadmin en `localStorage`).

## Risks / Trade-offs

- [RLS oculta filas a código sin contexto] → activar por tabla, probando en dev los flujos de pedidos, despacho, pagos y n8n antes de prod.
- [Usuario de BD actual es dueño/superusuario] → crear rol `fme_app` sin `BYPASSRLS` y cambiar `DATABASE_URL`; las migraciones siguen con el rol dueño.
- [Superadmins sin TOTP quedan fuera] → enrolar antes de activar la obligatoriedad; mantener un superadmin de emergencia vía CLI.

## Migration Plan

Fases 1→6 en orden, cada una en su propio PR y deploy. Rollback: cada migración tiene `downgrade` (RLS: `NO FORCE` + `DISABLE` + `DROP POLICY`).

## Open Questions

- ¿El acceso de soporte a un tenant debe ser solo lectura por defecto?
- ¿El POS pide el código de tenant en el login o lo trae configurado el dispositivo?
- Resuelto: tenants sin dominio propio (El Olivo y los actuales en `*.lexastech.cl`) pasan a `effichain-<slug>.effi4tech.cl`; los con dominio propio lo mantienen como alias.
- Resuelto: producto EffiChain, dominio de la empresa `effi4tech.cl`; consola en `effichain-admin.effi4tech.cl`.
