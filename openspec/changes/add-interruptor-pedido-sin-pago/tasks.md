# Tasks

## 1. Backend

- [x] 1.1 Columna `permitir_pedido_sin_pago` (default true) + migración `a4d9e2b7c1f6`; verificado `upgrade`/`downgrade`/`upgrade` en el contenedor
- [x] 1.2 Schemas de configuración y `permite_pedido_sin_pago` en `GET /api/tienda/entrega`; verificado dentro del contenedor (true por omisión, false al apagarlo)

## 2. Backoffice y landing

- [x] 2.1 Interruptor "Permitir pedidos sin pago en línea" en Configuración → Landing; `npx tsc` sin errores
- [x] 2.2 Checkout: ocultar la opción, aviso y botón deshabilitado sin pasarelas; `npx tsc` sin errores

## 3. Verificación

- [ ] 3.1 Prueba del usuario en local (tenant 1 local quedó con el interruptor apagado)
- [ ] 3.2 En prod: apagarlo para el tenant 1 solo cuando haya una pasarela en ambiente PRODUCCIÓN
