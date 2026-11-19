# Proposal

## Why

Masas Estación quiere que su tienda web cobre siempre en línea y dejar de ofrecer "Solicitar pedido sin pagar ahora". La landing es compartida por todos los tenants, así que el cambio debe ser por tenant, y no debe dejar la tienda sin salida mientras no haya una pasarela de producción.

## What Changes

- `configuracion_landing.permitir_pedido_sin_pago` (boolean, por omisión `true`), editable en Configuración → Landing del backoffice.
- `GET /api/tienda/entrega` devuelve `permite_pedido_sin_pago`.
- Checkout de la landing: si es `false`, no muestra la opción "Solicitar pedido sin pagar ahora"; si además no hay pasarelas disponibles, muestra "El pago en línea no está disponible en este momento. Contáctanos para hacer tu pedido." y deshabilita el envío.
- Si el pago falla después de crear el pedido, el pedido queda registrado y se coordina (comportamiento actual, sin cambios).

## Impact

- Backend: `database/models.py`, `schemas/configuracion_landing.py`, `routers/tarifas_delivery.py`, migración `a4d9e2b7c1f6`.
- Backoffice: `app/admin/configuracion/landing/page.tsx`, `lib/api/configuracion-landing.ts`.
- Landing: `app/checkout/page.tsx`, `lib/api/pedidos.ts`.
- Operación: apagarlo para el tenant 1 en prod solo cuando Khipu (u otra pasarela) esté en ambiente PRODUCCIÓN.
