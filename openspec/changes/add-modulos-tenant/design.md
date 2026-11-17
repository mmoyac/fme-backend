## Context

Ver proposal.md. Backend FastAPI + SQLAlchemy **síncrono** (nunca `async def` con la BD; incidente 2026-11-11). Menú: `menu_items` global + `role_menu_permissions` (rol↔menú), roles por tenant; `/api/auth/menu` devuelve `role.menus`. Routers montados en `main.py` con prefijos (`/api/despachos`, `/api/compras`, …); algunos (`pedidos`, `productos`, `payments`) atienden tanto al backoffice como a la landing pública (tenant resuelto por host vía `tenant_service`). Referencia: EffiCoop `platform/tenancy/modules.py` y `core/routing.py::require_module`.

## Goals / Non-Goals

**Goals:** catálogo en código, contratación por tenant, bloqueo en backend, menú filtrado.

**Non-Goals:** facturación/precios de planes; módulos con límites de uso (cupos); bloqueo por endpoint individual cuando el router entero ya pertenece a un módulo.

## Decisions

### D1. Catálogo en código, contratación en BD
`utils/modulos.py` define `NUCLEO`, `MODULOS` (código → nombre) y `REQUIERE` (código → set), como EffiCoop. No hay tabla de catálogo: agregar un módulo exige código de todas formas. Contratación en tabla `tenant_modulos (tenant_id, modulo, activado_en, activado_por)` con PK `(tenant_id, modulo)` y `CHECK modulo IN (...)`. Alternativa descartada: columna `ARRAY/JSON` en `tenants` (pierde quién/cuándo y la restricción por valor).

### D2. Validación de dependencias
`validar_modulos(set)` devuelve el primer faltante (`etiquetado` sin `produccion`) o el dependiente que impide quitar. Endpoint `PUT /api/superadmin/tenants/{id}/modulos` recibe el conjunto completo (idempotente) y aplica la diferencia en una transacción.

### D3. Dependencia `require_modulo(codigo)` por router
Se aplica en `main.py`: `app.include_router(despachos.router, ..., dependencies=[require_modulo("despacho")])`, igual que EffiCoop marca rutas. Resuelve el tenant así: usuario autenticado → `current_user.tenant_id` (respeta el contexto de superadmin); si no hay token → tenant por host (`tenant_service`). Consulta `tenant_modulos` (una query indexada por request; sin caché en esta fase). Es `def` síncrono.

Routers compartidos se resuelven por **endpoint**, no por router:
- `pedidos`: endpoints públicos de checkout → `tienda_online`; resto → `ventas`.
- `productos` / catálogo público de landing → `tienda_online` solo en endpoints públicos; los de backoffice son núcleo.
- `payments` → `tienda_online`.

Mapeo router → módulo (ajustado en la implementación, 2026-11-16):

| Módulo | Routers |
|---|---|
| ventas | pedidos (router completo; seguimiento público incluido), caja, `productos/catalogo-local` (POS) |
| cotizaciones | cotizaciones |
| preventa | preventa (+ router_pdf), stock_cajas |
| tienda_online | admin_configuracion_landing, paleta_colores; por endpoint: `POST /api/pedidos/` (checkout), `GET /api/productos/catalogo[/{sku}]`, `payments/create_preference` y `process_payment` (el webhook de MP no se bloquea) |
| inventario | inventario, movimientos_inventario, conteos_inventario, solicitudes_transferencia |
| compras | compras (incluye proveedores), precios_proveedor, enrolamiento (vehículos y lotes en recepción), gemini_vision (lectura de etiquetas en recepción) |
| produccion | produccion, recetas, ordenes_trabajo |
| etiquetado | etiquetas |
| despacho | despachos, hojas_ruta, vehiculos |
| cobranza | cobranza, notas_credito, devoluciones, cheques |
| comisiones | comisiones |
| fidelizacion | puntos |
| núcleo | auth, oauth, admin_users, admin_utils, clientes, productos (backoffice), precios, locales, maestras, configuracion, dashboard, alertas, notifications, tenants, superadmin, tipos_pedido, canales_venta, locales_cliente (maestras compartidas con la landing/clientes) |

### D4. Menú ligado a módulo
Columna `menu_items.modulo` (nullable = núcleo). `/api/auth/menu` filtra `role.menus` por módulos contratados. `PUT /api/admin/roles/{id}/menu` rechaza (422) ítems de módulos no contratados. Al quitar un módulo **no** se borran las asignaciones rol↔menú: solo se ocultan, así recontratar restaura el menú (escenario del spec). Pestañas de Mantenedores ligadas a un módulo (p. ej. `tipos_vehiculo` → despacho, `ot_etapas` → produccion) se filtran en el frontend con la lista de módulos de `/users/me`.

### D5. Migración
Crea `tenant_modulos`, agrega `menu_items.modulo`, rellena el módulo de los 21 ítems por `href`, e inserta los 12 módulos para cada tenant existente (`activado_por = 'migracion'`). `downgrade` elimina ambas cosas.

### D6. Errores
403 con `detail = {"code": "modulo_no_contratado", "modulo": "<codigo>", "mensaje": "..."}`. El backoffice muestra "Tu plan no incluye <módulo>"; la landing muestra una página de tienda no disponible.

- Si la request no tiene tenant resoluble (superadmin en modo plataforma, dominio no registrado) `require_modulo` no bloquea y deja que el endpoint responda como hoy.

## Risks / Trade-offs

- [Un endpoint queda en el módulo equivocado y bloquea un flujo] → la migración da todos los módulos a los tenants actuales; se prueba quitando módulos uno a uno en local antes de prod.
- [Routers compartidos backoffice/landing] → marcado por endpoint (D3) y prueba explícita del checkout con y sin `tienda_online`.
- [n8n y webhooks llaman APIs con API Key] → `require_modulo` resuelve tenant también desde `ApiKeyUser`; se prueba el workflow de emails.
- [Una query extra por request] → indexada por PK; si molesta, caché en memoria con invalidación al cambiar módulos.

## Migration Plan

1. Migración (todos los tenants con todos los módulos) → comportamiento idéntico.
2. Despliegue de `require_modulo` y filtro de menú → sin efecto visible.
3. Ajuste de módulos por tenant desde la consola.
Rollback: `alembic downgrade` y retirar las dependencias de `main.py`.

## Open Questions

Ninguna bloqueante: la lista de módulos fue aprobada por el usuario (2026-11-16).
