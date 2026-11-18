## Why

FME delega en n8n (`https://n8n.effi4tech.cl`) todos los correos a clientes (pedido confirmado, entregado, cotizaciones, código de verificación del checkout), un cron de limpieza y el agente de chat. Esa integración se construyó por partes, sin especificación: los contratos de los webhooks (URL, payload, cuándo se disparan) solo existen en el código y en la memoria de quien los hizo, y los workflows vivían únicamente dentro de n8n, sin respaldo. Desde el change `add-pasarelas-pago`, un workflow (`verificacion-email`) es además **crítico**: sin él la tienda no puede crear pedidos.

## What Changes

- Se documenta como spec base la **integración FME ↔ n8n**:
  - el contrato de cada webhook (URL, disparador en el backend, payload, guardas como preferencias de correo y canal de entrega inmediata);
  - la semántica de envío: fire-and-forget en un hilo, que nunca bloquea ni revierte la operación de negocio;
  - la excepción crítica: el código de verificación del checkout;
  - los flujos de n8n hacia el backend (cron de limpieza con `X-API-Key`).
- Se documenta la regla de **versionado de workflows**: todo workflow de FME se exporta a `n8n/workflows/` con `scripts/n8n_exportar.py`, sin secretos (`__SECRETO__:<nombre>`), con exclusión explícita de otros productos (`n8n/excluir.json`). Ya implementado el 2026-11-18.
- Se registran como deuda los puntos débiles observados, sin cambiar código en este change:
  - las URLs de los webhooks están escritas en el código, salvo la de verificación;
  - un envío fallido solo queda en el log, sin reintento;
  - la API key de integración está escrita a mano en el nodo del cron de limpieza.

## Capabilities

### New Capabilities
- `integracion-n8n`: contratos de los webhooks FME → n8n y de los flujos n8n → FME, semántica de envío, workflow crítico de verificación de correo, y versionado y manejo de secretos de los workflows en el repo.

### Modified Capabilities
<!-- Ninguna: documentación baseline de lo ya construido. -->

## Impact

- **Nuevo spec**: `openspec/specs/integracion-n8n/spec.md` (al archivar este change).
- **Código de referencia (no se modifica)**: `services/webhook_service.py`, `services/verificacion_email.py`, `routers/notifications.py` (`DELETE /api/notifications/cleanup`), `routers/cotizaciones.py`, `routers/hojas_ruta.py`, `routers/pedidos.py`, `services/pagos_online.py`.
- **Workflows versionados**: `n8n/workflows/*.json`, `n8n/excluir.json`, `n8n/README.md`, `scripts/n8n_exportar.py`.
- Capacitación: no aplica (integración técnica, sin pantallas).
