## MODIFIED Requirements

### Requirement: Transferencia directa entre locales
La pestaña Transferencias SHALL permitir transferir una cantidad mayor a 0, con hasta 3 decimales, de un producto desde un local de origen a un local de destino del tenant, con notas opcionales. La transferencia MUST descontar la cantidad del origen y sumarla al destino en la misma operación, protegida contra transferencias simultáneas sobre el mismo stock, y MUST registrar un movimiento tipo `TRANSFERENCIA` con origen, destino, cantidad, notas y el usuario autenticado.

#### Scenario: Transferencia exitosa
- **GIVEN** stock 20 en Lampa y 5 en TilTil
- **WHEN** el usuario transfiere 8 unidades de Lampa a TilTil
- **THEN** Lampa queda en 12, TilTil en 13, existe un movimiento `TRANSFERENCIA` de 8 con el nombre del usuario y se muestra el mensaje de éxito

#### Scenario: Destino sin inventario previo
- **GIVEN** el producto no tiene registro de inventario en el local de destino
- **WHEN** el usuario transfiere hacia ese local
- **THEN** se crea el registro de inventario en destino con la cantidad transferida

#### Scenario: Cantidad con decimales
- **GIVEN** 10,5 kg de un producto en Lampa
- **WHEN** el usuario transfiere 2,25 kg a TilTil
- **THEN** Lampa queda en 8,25 kg y TilTil aumenta en 2,25 kg

#### Scenario: Transferencias simultáneas
- **GIVEN** stock 10 en el origen
- **WHEN** dos usuarios transfieren 8 unidades desde ese origen al mismo tiempo
- **THEN** solo una se aplica y la otra se rechaza por stock insuficiente
