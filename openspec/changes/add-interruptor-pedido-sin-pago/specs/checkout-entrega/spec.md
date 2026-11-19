# Spec Delta

## ADDED Requirements

### Requirement: Interruptor de pedido sin pago en línea por tenant
Cada tenant SHALL poder activar o desactivar la opción "Solicitar pedido sin pagar ahora" del checkout. Por omisión SHALL estar activa. Si está desactivada y no hay pasarelas disponibles, el checkout MUST impedir enviar el pedido e informar que el pago en línea no está disponible.

#### Scenario: Interruptor activo
- **WHEN** el tenant tiene el interruptor activo
- **THEN** el checkout ofrece las pasarelas disponibles y "Solicitar pedido sin pagar ahora"

#### Scenario: Interruptor apagado con pasarela
- **WHEN** el tenant apagó el interruptor y tiene una pasarela de producción activa
- **THEN** el checkout solo ofrece pagar en línea

#### Scenario: Interruptor apagado sin pasarela
- **WHEN** el tenant apagó el interruptor y no hay pasarelas disponibles
- **THEN** el checkout muestra "El pago en línea no está disponible en este momento. Contáctanos para hacer tu pedido." y el botón de envío queda deshabilitado

#### Scenario: Otros tenants
- **WHEN** el tenant A apaga el interruptor
- **THEN** el checkout del tenant B no cambia
