## Why

Al pagar con Mercado Pago en el checkout (`masasestacion.cl/checkout`), el cliente recibe el mensaje genérico **"Error interno del servidor"** y no puede completar la compra. El flujo "pago coordinado" sí funciona. El mensaje es el fallback del middleware CORS para excepciones no controladas, por lo que la causa real queda oculta para el usuario y solo visible en el traceback del servidor. Mientras tanto, se pierden ventas por la pasarela de pago principal.

## What Changes

- **Recuperar la causa raíz**: inspeccionar el traceback que el middleware registra (`logger.error` en `main.py`) para identificar la excepción exacta que se lanza al pagar con `medio_pago_codigo = "MERCADOPAGO"`.
- **Endurecer el endpoint de creación de pedido** (`POST /api/pedidos/`): envolver el flujo en manejo de excepciones que distinga errores de validación/negocio (4xx con mensaje claro) de errores inesperados, en lugar de dejar que cualquier excepción caiga al middleware como 500 genérico.
- **Endurecer el endpoint de pago** (`POST /api/payments/process_payment`): propagar el error real de Mercado Pago (rechazos, token mal configurado, datos faltantes) con un detalle accionable, no `str(e)` opaco ni 500 genérico.
- **Mejorar la observabilidad**: que los errores del flujo de pago queden logueados con contexto (pedido_id / external_reference, medio de pago) para diagnóstico futuro.
- Tarea secundaria en `fme-landing`: el checkout debe mostrar el `detail` real del backend al usuario (no enmascararlo con un `alert` genérico) y manejar correctamente los estados de pago rechazado/pendiente.

## Capabilities

### New Capabilities
- `checkout-pago`: Comportamiento esperado del flujo de pago del checkout (creación de pedido con medio de pago, procesamiento del pago con Mercado Pago, y reglas de manejo y reporte de errores hacia el cliente).

### Modified Capabilities
<!-- No hay specs existentes de checkout/pagos que modificar -->

## Impact

- **Backend** (`fme-backend`):
  - `routers/pedidos.py` → `crear_pedido_frontend` (`POST /api/pedidos/`)
  - `routers/payments.py` → `process_payment`, `create_payment_preference`
  - `services/payment_service.py` → `process_payment`, `create_preference`
  - `main.py` → middleware de manejo de excepciones (observabilidad)
- **Frontend** (`fme-landing`, fuera de este repo, tarea coordinada):
  - `app/checkout/page.tsx` (manejo y despliegue de errores)
  - `lib/api/pedidos.ts`, `components/MercadoPagoBrick.tsx`
- **Dependencias**: SDK de Mercado Pago, variable de entorno `MP_ACCESS_TOKEN`.
- Sin cambios de esquema de base de datos.
