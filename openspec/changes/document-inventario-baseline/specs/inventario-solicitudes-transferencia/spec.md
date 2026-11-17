# Spec Delta

## Purpose

Permite que un local pida productos a otro local del mismo tenant, que el local que despacha apruebe las cantidades y mueva el stock, y que el local que pidió registre lo que efectivamente recibió. Complementa la transferencia directa con un flujo de pedido y aprobación entre tiendas.

## ADDED Requirements

### Requirement: Crear solicitud entre locales
Un usuario SHALL poder crear una solicitud con una nota opcional y una lista de productos con cantidad solicitada, donde el local que pide (destino) es su local por defecto y el local que despacha (origen) se elige entre los demás locales del tenant, excluyendo el local WEB. La solicitud nace en estado `PENDIENTE` y notifica al local origen.

#### Scenario: Solicitud creada
- **GIVEN** un usuario con local por defecto TilTil
- **WHEN** solicita 10 unidades de un producto a Lampa
- **THEN** existe una solicitud `PENDIENTE` con destino TilTil, origen Lampa y el usuario como solicitante, y Lampa recibe una notificación

### Requirement: Estados y transiciones
Las solicitudes SHALL seguir los estados `PENDIENTE` → `EN_PROCESO` → `FINALIZADO`. El local origen (o un admin) pasa de PENDIENTE a EN_PROCESO ("Comenzar atención") y de EN_PROCESO a FINALIZADO; el local destino puede editar la nota y los productos solo mientras está PENDIENTE. Cualquier otra edición MUST rechazarse con 403.

#### Scenario: Comenzar atención
- **WHEN** un usuario del local origen comienza la atención de una solicitud PENDIENTE
- **THEN** pasa a EN_PROCESO y el local destino recibe una notificación

#### Scenario: Destino intenta aprobar
- **WHEN** un usuario del local destino intenta cambiar el estado o fijar cantidades aprobadas
- **THEN** el sistema responde 403

### Requirement: Finalizar mueve stock
Al pasar de EN_PROCESO a FINALIZADO, el sistema SHALL registrar la cantidad aprobada de cada producto y, por cada producto con cantidad aprobada mayor a 0, descontarla del local origen, sumarla al local destino y registrar un movimiento `TRANSFERENCIA` que referencia la solicitud, todo en una sola operación; registra al usuario finalizador y notifica al destino.

#### Scenario: Finalizar con aprobación parcial
- **GIVEN** una solicitud EN_PROCESO de 10 unidades
- **WHEN** el origen finaliza aprobando 8
- **THEN** el origen baja 8, el destino sube 8 y existe un movimiento `TRANSFERENCIA` de 8 con referencia a la solicitud

### Requirement: Registrar recepción
Con la solicitud FINALIZADA, el local destino (o un admin) SHALL poder registrar la cantidad recibida de cada producto; si lo recibido es menor que lo aprobado, la diferencia se devuelve al stock del origen y se descuenta del destino. Queda registrado quién recibió y cuándo.

#### Scenario: Recepción con faltante
- **GIVEN** una solicitud finalizada con 8 aprobadas
- **WHEN** el destino registra 7 recibidas
- **THEN** el origen recupera 1, el destino queda con 1 menos y la solicitud queda marcada como recibida

### Requirement: Listado y visibilidad
El listado SHALL mostrar las solicitudes del tenant; un usuario no admin con local por defecto ve solo las solicitudes donde su local es origen o destino. Por defecto se muestran las activas (no finalizadas, o finalizadas aún no recibidas por el local del usuario), con filtro por estado y vistas de detalle, PDF y compartir.

#### Scenario: Usuario de tienda
- **GIVEN** un usuario no admin con local por defecto TilTil
- **WHEN** abre Solicitudes
- **THEN** solo ve solicitudes donde TilTil es origen o destino

### Requirement: Indicador de despacho
El local origen (o un admin) SHALL poder marcar si la solicitud requiere delivery mientras no haya sido recibida.

#### Scenario: Marcar delivery
- **WHEN** el origen marca "requiere delivery" en una solicitud finalizada no recibida
- **THEN** la solicitud muestra la etiqueta "Requiere delivery"
