# Proposal

## Why

La tienda online hoy solo permite despacho y no informa cuánto cuesta: el cliente no sabe el valor del delivery ni puede
elegir retirar en la casa central (Lampa). Con el pago en línea (change `add-pasarelas-pago`) el delivery además debe
cobrarse en el mismo pago. En paralelo, se necesita mostrar a un cliente el checkout con pago (Khipu) en producción antes
de tener la cuenta de cobro real, y hoy el backend oculta en producción toda pasarela de Integración.

## What Changes

- Nuevo mantenedor de **tarifas de delivery por comuna** (por tenant) en el backoffice: comuna, costo, activa.
- El checkout de la landing pide la **modalidad de entrega**: **Retiro en casa central** (muestra la dirección, sin costo)
  o **Delivery**. Con delivery, el cliente elige su comuna de la lista de comunas con tarifa y ve el costo y el total
  antes de enviar. Comunas sin tarifa no tienen delivery.
- Envío gratis sobre el monto mínimo ya configurable (`monto_minimo_delivery_gratis` de la configuración de la landing).
- El backend **recalcula** el costo de delivery desde la tabla (nunca confía en el monto que envía el navegador) y lo
  guarda en el pedido (`costo_delivery`, `comuna_entrega`, `modalidad_entrega`).
- El **pago en línea cobra productos + delivery**. (Hoy la intención cobra solo `monto_total`.)
- **Modo demo de pasarelas** en producción: con la variable `PASARELAS_CLAVE_DEMO` definida, quien entra a la landing con
  `?demo=<clave>` ve y puede usar las pasarelas de ambiente Integración (nunca la Simulada). Sin la clave, nada cambia.
- **BREAKING (comportamiento):** la tienda online deja de crear siempre pedidos DESPACHO; ahora la modalidad la elige el
  cliente. El campo `modalidad_entrega` del pedido de la landing pasa a ser obligatorio en la API.

## Capabilities

### New Capabilities
- `tarifas-delivery`: tarifas de delivery por comuna del tenant, su mantenimiento y el cálculo del costo de un pedido.
- `checkout-entrega`: elección de retiro o delivery en el checkout de la tienda y cómo queda en el pedido.

### Modified Capabilities
- `pasarelas-pago` (creada por `add-pasarelas-pago`, aún sin archivar): el monto de la intención incluye el delivery; se
  agrega el modo demo para pasarelas de Integración en producción.
- `pedido-entrega` (creada por `add-modalidad-entrega-pedido`, aún sin archivar): el pedido de la tienda online toma la
  modalidad elegida por el cliente en lugar de ser siempre DESPACHO.

## Impact

- **Backend:** modelo y migración (`tarifas_delivery`, `pedidos.comuna_entrega`), router nuevo de tarifas (admin y
  público), `routers/pedidos.py` (`crear_pedido_frontend`), `schemas/pedido.py`, `services/pagos_online.py`,
  `routers/pagos_online.py`, `services/pasarelas/config.py`, `docker-compose.prod.yml`, `docs/PASARELAS_PAGO.md`.
- **Backoffice:** pantalla nueva Mantenedores → Tarifas de delivery; detalle de pedido muestra comuna y costo de delivery.
- **Landing:** `app/checkout/page.tsx`, `lib/api/pedidos.ts`, `lib/api/pagos.ts` (clave demo en `sessionStorage`).
- **n8n:** sin cambios de workflow (el correo de confirmación ya recibe el pedido; mostrar el delivery en el correo
  queda fuera de este change).
- **Capacitación:** no hay lecciones de pedidos ni tienda en `capacitacion/`; no se afectan lecciones existentes.
- **Orden de archivo:** archivar después de `add-modalidad-entrega-pedido` y `add-pasarelas-pago`, porque modifica sus specs.
