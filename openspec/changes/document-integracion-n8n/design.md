# Design

## Contexto
- Instancia: `https://n8n.effi4tech.cl`, compartida con otros productos (EffiCheck, Effiguard). Los workflows
  de Masas Estación se migraron desde `n8n.masasestacion.cl` conservando sus IDs.
- Acceso de herramientas: MCP `n8n-effi4tech` (scope user, `~/.claude.json`) o API REST `/api/v1` con header
  `X-N8N-API-KEY`.

## Inventario (2026-11-18)

| Workflow (ID) | Webhook / disparo | Dirección |
|---|---|---|
| Email Confirmación Compra (`8k3qYK9sfm1NEA1R`) | `POST /webhook/pedido-confirmado` | FME → n8n |
| Email Entrega Pedido (`AqmOmlWJETP1WGAZ`) | `POST /webhook/pedido-entregado` | FME → n8n |
| Email Cotización Creada (`jxqf6tbbLaMBkS1W`) | `POST /webhook/cotizacion-creada` | FME → n8n |
| Email Cotización Enviada (`83wJG86ubVIbIIgf`) | `POST /webhook/cotizacion-enviada` | FME → n8n |
| Email Cotización Aceptada (`slz6kRggfUkeBu3H`) | `POST /webhook/cotizacion-aceptada` | FME → n8n |
| Código de verificación de correo (`VxFbcw9rerVw1ByA`) | `POST /webhook/verificacion-email` | FME → n8n (**crítico**) |
| Limpieza Notificaciones (`utisRGKMxY1kKAjJ`) | cron → `DELETE /api/notifications/cleanup` | n8n → FME |
| Agente Chat (`n26TaZhlycsY7xcA`) | chat de n8n → `GET /api/productos/catalogo` | n8n → FME |
| Catálogo de Productos (`Ojcal1wIkrB0i1C5`) | inactivo | — |

## Decisiones
1. **Fire-and-forget**: `webhook_service._post_webhook` corre en un hilo daemon con timeout de 10 s. Si falla,
   queda un warning en el log y la operación de negocio sigue: un correo no enviado no debe deshacer un pedido o un pago.
2. **Excepción crítica (verificación de correo)**: el envío también es asíncrono, pero el pedido de la tienda
   **depende** del código. Si n8n no lo envía, el cliente no puede comprar. Por eso:
   - en desarrollo el código se escribe en el log;
   - su URL se puede configurar con `N8N_WEBHOOK_VERIFICACION_EMAIL`;
   - el workflow está marcado como crítico en el README y en las tareas.
3. **Datos en el payload**:
   - solo lo necesario para el correo;
   - fechas ya formateadas en hora de Chile;
   - `unsub_url` (baja de correos) y `seguimiento_url` cuando aplica;
   - nunca credenciales ni datos de pago.
   El código de verificación sí viaja en claro a n8n, porque es el canal que lo entrega; en la base solo se guarda su HMAC.
4. **Versionado**:
   - `scripts/n8n_exportar.py` exporta todo lo no excluido;
   - formato estable (sin fechas ni `versionId`, claves ordenadas, sin `id` de nodo);
   - credenciales solo como referencia `{id, name}`;
   - claves escritas en los nodos → `__SECRETO__:<nombre>`;
   - `--verificar` sirve para CI o revisión.

## Deuda observada (fuera de alcance; candidatos a changes)
- URLs de webhooks escritas en `webhook_service.py`: deberían salir de variables de entorno, como la de verificación.
- Sin reintentos ni registro persistente de envíos fallidos (solo log).
- La API key de integración está escrita en el nodo HTTP del cron de limpieza: moverla a una credencial n8n de tipo
  *Header Auth*.
- `seguimiento_url` apunta a un dominio fijo (`seguimiento.lexastech.cl`), no por tenant.
