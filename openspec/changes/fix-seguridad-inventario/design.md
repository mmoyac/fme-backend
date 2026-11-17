## Context

Ver `document-inventario-baseline/design.md` (sección Seguridad). Hoy `main.py` registra el router de solicitudes solo con `require_modulo("inventario")`, que no autentica; `POST /`, `GET /{id}` y `DELETE /{id}` no declaran `get_current_active_user`. `GET /` resuelve el tenant por hostname. En `stock_cajas.py` las escrituras buscan por `producto_id`/`proveedor_id` sin join a `Producto.tenant_id`.

## Goals / Non-Goals

**Goals:** cerrar acceso anónimo y cruce entre tenants con el menor cambio posible.

**Non-Goals:** validaciones de negocio (stock, origen≠destino), decimales o UI — van en `improve-solicitudes-transferencia` y `fix-inventario-movimientos-trazabilidad`.

## Decisions

- **Auth a nivel de router**: agregar `Depends(get_current_active_user)` en el `include_router` de solicitudes (igual que inventario y movimientos) y además en cada endpoint para tener `current_user`.
- **Tenant desde el usuario**, no del hostname: consistente con el resto de la API y con el contexto de superadmin (`_aplicar_contexto_tenant`).
- **Helper `_obtener_solicitud(db, id, user)`** que filtra por `tenant_id` y responde 404; lo usan GET, PUT y DELETE.
- **Stock de Cajas**: helper que valida `Producto.tenant_id == current_user.tenant_id` antes de escribir.
- Endpoints `def` síncronos.

## Risks / Trade-offs

- [Algún cliente externo (n8n, scripts) llamaba sin token] → buscar llamadas en n8n y scripts antes del deploy; recibirán 401.
- [Usuarios superadmin operando en contexto de tenant] → se usa `current_user.tenant_id`, que ya refleja el contexto.

## Migration Plan

Sin migraciones. Deploy solo backend (el backoffice sigue funcionando). Rollback: revertir el commit.
