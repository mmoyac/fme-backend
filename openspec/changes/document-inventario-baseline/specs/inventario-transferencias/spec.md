# Spec Delta

## Purpose

Permite mover stock de un producto desde un local a otro del mismo tenant en una sola operación, validando disponibilidad y dejando registrado el movimiento para el historial.

## ADDED Requirements

### Requirement: Transferencia directa entre locales
La pestaña Transferencias SHALL permitir transferir una cantidad entera mayor a 0 de un producto desde un local de origen a un local de destino del tenant, con notas opcionales. La transferencia MUST descontar la cantidad del origen y sumarla al destino en la misma operación, y MUST registrar un movimiento tipo `TRANSFERENCIA` con origen, destino, cantidad y notas.

#### Scenario: Transferencia exitosa
- **GIVEN** stock 20 en Lampa y 5 en TilTil
- **WHEN** el usuario transfiere 8 unidades de Lampa a TilTil
- **THEN** Lampa queda en 12, TilTil en 13, existe un movimiento `TRANSFERENCIA` de 8 y se muestra el mensaje de éxito

#### Scenario: Destino sin inventario previo
- **GIVEN** el producto no tiene registro de inventario en el local de destino
- **WHEN** el usuario transfiere hacia ese local
- **THEN** se crea el registro de inventario en destino con la cantidad transferida

### Requirement: Validaciones de transferencia
El sistema SHALL rechazar la transferencia, sin modificar stock, cuando el origen y el destino son el mismo local, cuando el producto no tiene inventario en el origen o cuando la cantidad supera el stock disponible en el origen.

#### Scenario: Mismo local
- **WHEN** el usuario elige el mismo local como origen y destino
- **THEN** el sistema responde 400 "El local de origen y destino deben ser diferentes"

#### Scenario: Stock insuficiente
- **GIVEN** stock 4 en el origen
- **WHEN** el usuario intenta transferir 6
- **THEN** el sistema responde 400 indicando el stock disponible y nada cambia

#### Scenario: Sin inventario en origen
- **WHEN** el producto no tiene registro de inventario en el local de origen
- **THEN** el sistema responde 400 indicando que no tiene inventario en ese local

### Requirement: Vista previa de la transferencia
Mientras el usuario completa el formulario, la pestaña SHALL mostrar el stock disponible en origen, el stock actual en destino y un resumen con el stock resultante de ambos locales; tras una transferencia exitosa el formulario se limpia y los stocks se recargan.

#### Scenario: Resumen previo
- **GIVEN** stock 20 en origen y 5 en destino
- **WHEN** el usuario ingresa cantidad 8
- **THEN** el resumen muestra origen 20 → 12 y destino 5 → 13

### Requirement: Aislamiento por tenant en transferencias
La transferencia MUST operar solo con productos y locales del tenant del usuario autenticado.

#### Scenario: Local de otro tenant
- **WHEN** el usuario intenta transferir hacia o desde un local que no pertenece a su tenant
- **THEN** el sistema responde 404 y no modifica stock
