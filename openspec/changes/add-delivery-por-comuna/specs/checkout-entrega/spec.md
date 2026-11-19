# Spec Delta

## Purpose

Permite al cliente de la tienda online elegir cómo recibe su pedido (retiro en la casa central o delivery a su comuna),
conocer el costo antes de confirmar y que esa elección quede registrada en el pedido.

## ADDED Requirements

### Requirement: Elección de modalidad en el checkout
El checkout de la tienda SHALL pedir al cliente elegir entre "Retiro en casa central", mostrando la dirección de retiro,
y "Delivery". Con delivery SHALL pedir la dirección y la comuna, elegida de la lista de comunas con tarifa activa.

#### Scenario: Cliente elige retiro
- **WHEN** el cliente elige "Retiro en casa central"
- **THEN** ve la dirección de retiro, no se le pide dirección de entrega y el resumen muestra delivery $0

#### Scenario: Cliente elige delivery
- **WHEN** el cliente elige "Delivery" y la comuna "Colina"
- **THEN** el resumen muestra el costo de delivery de Colina y el total (productos + delivery) antes de enviar

#### Scenario: Dirección elegida del autocompletar
- **WHEN** el cliente escribe su dirección y elige una sugerencia del mapa ubicada en Lampa, comuna con tarifa
- **THEN** la comuna queda en Lampa, el checkout muestra la dirección como encontrada y no pide confirmación manual

#### Scenario: Sugerencia en comuna sin delivery
- **WHEN** el cliente elige una sugerencia ubicada en una comuna sin tarifa
- **THEN** el checkout avisa que no hay delivery a esa comuna y no deja comuna seleccionada

#### Scenario: Confirmación manual de la comuna
- **WHEN** el cliente escribe la dirección sin elegir una sugerencia y elige la comuna "Lampa"
- **THEN** el campo indica "Dirección en Lampa" y el checkout no permite enviar hasta que el cliente marque que su dirección está en Lampa y que, si no corresponde, el pedido puede reprogramarse o cobrarse la diferencia

#### Scenario: Sin comunas con tarifa
- **WHEN** el tenant no tiene tarifas activas
- **THEN** el checkout ofrece solo "Retiro en casa central"

### Requirement: Registro de la entrega en el pedido de la tienda
Al crear un pedido de la tienda, el backend SHALL exigir la modalidad (RETIRO o DESPACHO), recalcular el costo de
delivery desde las tarifas del tenant ignorando cualquier monto enviado por el navegador, y guardar en el pedido la
modalidad, la comuna de entrega y el costo de delivery.

#### Scenario: Pedido con delivery
- **WHEN** se crea un pedido DESPACHO a "Colina" (tarifa $3.000)
- **THEN** el pedido queda con `modalidad_entrega = DESPACHO`, `comuna_entrega = Colina` y `costo_delivery = 3000`

#### Scenario: Pedido con retiro
- **WHEN** se crea un pedido RETIRO
- **THEN** el pedido queda con `modalidad_entrega = RETIRO`, sin comuna de entrega y `costo_delivery = 0`

#### Scenario: Dirección verificada en el mapa
- **WHEN** se crea un pedido DESPACHO cuya dirección el servicio de mapas ubica con alta confianza en la comuna elegida
- **THEN** el pedido se crea sin exigir confirmación manual y las notas internas indican "Dirección verificada"

#### Scenario: Dirección en otra comuna
- **WHEN** el servicio de mapas ubica con alta confianza la dirección en una comuna distinta de la elegida
- **THEN** el sistema responde 400 indicando la comuna real y no crea el pedido

#### Scenario: Dirección no verificable
- **WHEN** el servicio de mapas no encuentra la dirección con confianza (o no está disponible)
- **THEN** el sistema exige la confirmación del cliente (400 sin ella) y, con ella, crea el pedido con la nota interna "Dirección NO verificada: revisar antes de despachar"

#### Scenario: Modalidad faltante
- **WHEN** la petición no trae `modalidad_entrega` válida
- **THEN** el sistema responde 422 y no crea el pedido
