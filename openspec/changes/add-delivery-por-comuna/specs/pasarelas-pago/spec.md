# Spec Delta

## MODIFIED Requirements

### Requirement: Pago en línea de un pedido de la tienda
Tras crear el pedido, la landing SHALL poder iniciar su pago con una pasarela disponible presentando `pedido_id` y `token_seguimiento`. El monto SHALL fijarlo el backend desde el pedido: productos (`monto_total`) más `costo_delivery`. La intención SHALL vencer a los 15 minutos.

#### Scenario: Iniciar pago
- **WHEN** la landing envía un pedido pendiente y no pagado con su token y una pasarela disponible
- **THEN** el sistema crea la intención, la registra en el proveedor y devuelve la redirección

#### Scenario: Token inválido o pedido pagado
- **WHEN** el token no corresponde al pedido o el pedido ya está pagado o cancelado
- **THEN** el sistema responde 404 o 400 sin contactar al proveedor

#### Scenario: Pedido con delivery
- **WHEN** se inicia el pago de un pedido de $8.000 en productos con delivery de $3.000
- **THEN** la intención y el cobro en el proveedor son por $11.000

## ADDED Requirements

### Requirement: Modo demo de pasarelas en producción
Si el servidor tiene configurada una clave demo, las peticiones públicas de opciones de pago y de inicio de pago que
presenten esa clave SHALL tratar como disponibles también las pasarelas activas de ambiente INTEGRACION. La pasarela
Simulada NUNCA SHALL ofrecerse en producción. Sin clave configurada, o con una clave incorrecta, el comportamiento SHALL
ser el normal de producción.

#### Scenario: Visitante con enlace demo
- **WHEN** el backend corre en producción con clave demo configurada y la landing pide las opciones con la clave correcta
- **THEN** recibe las pasarelas activas de PRODUCCION y de INTEGRACION, sin la Simulada

#### Scenario: Visitante normal
- **WHEN** la landing pide las opciones sin clave o con una clave incorrecta
- **THEN** recibe solo las pasarelas activas de PRODUCCION

#### Scenario: Servidor sin clave demo
- **WHEN** la clave demo no está configurada en el servidor
- **THEN** ninguna petición puede usar pasarelas de INTEGRACION en producción
