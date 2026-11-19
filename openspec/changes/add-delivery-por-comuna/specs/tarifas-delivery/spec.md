# Spec Delta

## Purpose

Define el costo de delivery de la tienda online por comuna, configurado por cada tenant, y cómo se calcula el costo de
delivery de un pedido a partir de esa tabla.

## ADDED Requirements

### Requirement: Mantenedor de tarifas por comuna
Un administrador del tenant SHALL poder crear, editar, activar/desactivar y eliminar tarifas de delivery, cada una con
nombre de comuna y costo en pesos (entero, mayor o igual a 0). La comuna SHALL ser única por tenant sin distinguir
mayúsculas, tildes ni espacios extremos. Las tarifas de un tenant NUNCA SHALL ser visibles ni editables desde otro tenant.

#### Scenario: Crear tarifa
- **WHEN** el administrador crea la tarifa "Colina" con costo 3000
- **THEN** la tarifa queda activa y aparece en la lista del tenant

#### Scenario: Comuna duplicada
- **WHEN** el administrador crea "colina " y ya existe "Colina" en su tenant
- **THEN** el sistema responde 409 y no crea la tarifa

#### Scenario: Costo inválido
- **WHEN** el costo es negativo o no es un número entero
- **THEN** el sistema responde 422

### Requirement: Comunas con delivery para la tienda
El sistema SHALL exponer públicamente, para el tenant del dominio, las tarifas activas (comuna y costo, ordenadas por
comuna), el monto mínimo para envío gratis si está configurado, y la dirección de retiro de la casa central.

#### Scenario: Consulta desde la landing
- **WHEN** la landing pide las opciones de entrega
- **THEN** recibe solo las tarifas activas de su tenant, el monto mínimo para envío gratis (o nulo) y la dirección de retiro

### Requirement: Cálculo del costo de delivery de un pedido
El costo de delivery de un pedido DESPACHO de la tienda SHALL ser la tarifa activa de su comuna, o 0 si el monto de los
productos (después de descuentos) alcanza el monto mínimo para envío gratis. Un pedido RETIRO SHALL tener costo 0.

#### Scenario: Comuna con tarifa
- **WHEN** se calcula el delivery de un pedido de $8.000 a "Colina" (tarifa $3.000) sin mínimo de envío gratis
- **THEN** el costo de delivery es $3.000

#### Scenario: Envío gratis
- **WHEN** el monto mínimo para envío gratis es $30.000 y los productos suman $35.000
- **THEN** el costo de delivery es $0

#### Scenario: Comuna sin tarifa
- **WHEN** la comuna no tiene tarifa activa en el tenant
- **THEN** el sistema rechaza el pedido con 400 "No hay delivery a esa comuna"
