## Why

El pago en línea de la tienda (landing) usaba el Payment Brick de Mercado Pago con problemas graves:

- **El monto lo decidía el navegador**: `POST /api/payments/process_payment` reenviaba a Mercado Pago el cuerpo recibido (monto y `external_reference` incluidos) y, si salía aprobado, marcaba el pedido como pagado sin comparar el monto con el pedido.
- `POST /api/test/test_webhook/{pedido_id}` (router "TEST ONLY") estaba montado en producción **sin autenticación** y marcaba cualquier pedido como pagado.
- Una sola cuenta de Mercado Pago para todos los tenants (token en variable de entorno, versionado en `docker-compose.yml`), `notification_url` fija, sin `X-Idempotency-Key`, sin conciliación (un aviso perdido dejaba el pedido sin pagar) y `pedido.estado = "CONFIRMADO"` sin efecto (no es columna).

EffiCheck tiene una arquitectura multipasarela probada en producción (Flow y Khipu): adaptador por proveedor, credenciales cifradas por tenant, verificación servidor a servidor, confirmación idempotente y conciliación. Este change la porta a FME.

## What Changes

- **Nuevo paquete `services/pasarelas/`** (portado de EffiCheck): contrato `Adaptador`, cifrado AES-256-GCM, adaptadores **Flow**, **Khipu**, **Simulada** y uno nuevo de **Mercado Pago (Checkout Pro)**. Un proveedor nuevo = un adaptador nuevo.
- **Nuevas tablas** `pasarelas_pago` (por tenant, ambiente INTEGRACION/PRODUCCION, credenciales cifradas, prueba de conexión) y `pagos_online` (intención de pago de un pedido). Medios de pago FLOW, KHIPU y PAGO_ONLINE (inactivos).
- **Núcleo `services/pagos_online.py`**: intención con vencimiento de 15 min, monto fijado por el backend desde el pedido, confirmación idempotente con `FOR UPDATE`, monto distinto → EN_REVISION, pedido ya pagado/cancelado → EN_REVISION, conciliación cada 2 min en un hilo de fondo (con `pg_try_advisory_lock`).
- **Endpoints** públicos `/api/pagos/*` (opciones, crear, estado, consultar, simulada, retorno, webhook) y de administración `/api/admin/pasarelas/*`.
- `POST /api/pedidos/` devuelve `token_seguimiento` (credencial para iniciar el pago de ese pedido).
- **BREAKING**: se eliminan `routers/payments.py` (`/api/payments/*`), `routers/test_payments.py` (`/api/test/test_webhook`) y `services/payment_service.py`.
- Variables de entorno nuevas: `ENTORNO` (ausente = producción), `PASARELAS_CLAVE_MAESTRA`, `URL_PUBLICA_PAGOS` (solo desarrollo), `URL_API_PUBLICA` (opcional).
- **fme-landing**: el checkout lista las pasarelas activas y redirige al proveedor; nuevas páginas `/checkout/resultado` y `/checkout/simulada`; se elimina el Payment Brick.
- **fme-backoffice**: pantalla Mantenedores → Pasarelas de pago (`/admin/configuracion/pasarelas`).
- **Ampliaciones del 2026-11-18, durante la prueba en local:**
  - **Confirmación automática** del pedido pagado (descuenta inventario del local de despacho por defecto). Si no puede, el pedido queda pagado y PENDIENTE y se notifica a los admins.
  - **Correo del checkout validado**: formato, dominio con MX y sugerencia de errores de tipeo.
  - **Correo verificado con código de 6 dígitos** vía n8n. `POST /api/pedidos/` exige `email_token`. Tabla `verificaciones_email`. Workflow n8n `VxFbcw9rerVw1ByA` (crítico).
  - **Dashboard**: tarjeta "Por entregar" (`GET /api/dashboard/por-entregar`).
  - **Pedidos**: filtros EN_RUTA y `pagado`, filtros desde la URL, y "Creado por" muestra 🛒 Tienda online.
  - Se quita del `docker-compose.yml` el access token de Mercado Pago (hay que rotarlo).

## Capabilities

### New Capabilities
- `pasarelas-pago`: configuración de pasarelas por tenant, pago en línea de pedidos de la tienda, confirmación automática y notificaciones.
- `checkout-correo`: validación del correo del checkout y verificación con código.
- `pedidos-por-entregar`: resumen "Por entregar" del dashboard y filtros y origen en el listado de pedidos.

### Modified Capabilities
<!-- Reemplaza el comportamiento descrito en el change fix-checkout-mercadopago-500 (requisito "Procesamiento de pago con Mercado Pago"), que no fue archivado. -->

## Impact

- Backend: `services/pasarelas/*`, `services/pagos_online.py`, `routers/pagos_online.py`, `database/models.py`, migración `b7e2a9c4d1f3`, `main.py`, `routers/pedidos.py`, `schemas/pedido.py`, `docker-compose.yml`, `tests/test_pasarelas.py`.
- Landing: `app/checkout/page.tsx`, `app/checkout/resultado`, `app/checkout/simulada`, `lib/api/pagos.ts`, `lib/api/pedidos.ts`; se elimina `components/MercadoPagoBrick.tsx`.
- Backoffice: `app/admin/configuracion/pasarelas`, `lib/api/pasarelas.ts`, `app/admin/mantenedores/page.tsx`, `app/admin/dashboard/page.tsx`, `app/admin/pedidos/page.tsx`, `lib/api/dashboard.ts`, `lib/api/pedidos.ts`.
- Backend (ampliaciones): `utils/email_check.py`, `services/verificacion_email.py`, migración `c4f8e2d6b1a9`, `services/notification_service.py` (`notify_admins_tenant`), `routers/dashboard.py`, `routers/pedidos.py` (validar-email, verificacion-email, filtro `pagado`, canal de venta).
- n8n: workflow `verificacion-email` (registrado en la spec `integracion-n8n`, change `document-integracion-n8n`).
- Guía de operación: `docs/PASARELAS_PAGO.md`. `MERCADOPAGO_INTEGRATION.md` quedó obsoleto.
- Reemplaza el change `fix-checkout-mercadopago-500` en lo que toca al pago (el endpoint que corregía fue eliminado).
- Producción: definir `PASARELAS_CLAVE_MAESTRA` (y `URL_API_PUBLICA=https://api.masasestacion.cl` si el proxy no envía `X-Forwarded-Proto`) en el `.env` del VPS; configurar la pasarela en el backoffice.
- El pedido pagado en línea queda `es_pagado = true` con su medio de pago y se **confirma automáticamente** (descuenta inventario del local de despacho por defecto). Si falta stock en ese local, queda PENDIENTE y se notifica a los admins.
- Capacitación: el módulo de ventas/tienda online aún no tiene lecciones → pendiente (ver tasks).
