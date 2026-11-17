## MODIFIED Requirements

### Requirement: Registro de merma
Existencias SHALL permitir registrar una merma (pérdida, daño, vencimiento) para un producto en un local físico, indicando una cantidad mayor a 0 con hasta 3 decimales y un motivo opcional. La merma MUST descontar la cantidad del stock del local, MUST NOT dejar stock negativo y MUST registrar un movimiento tipo `MERMA` con el usuario que la realizó.

#### Scenario: Merma válida
- **GIVEN** stock 10 del producto en Lampa
- **WHEN** el usuario registra una merma de 3 con motivo "Producto vencido"
- **THEN** el stock queda en 7 y existe un movimiento `MERMA` de 3 con el motivo y el nombre del usuario

#### Scenario: Merma con decimales
- **GIVEN** stock 5 kg del producto en Lampa
- **WHEN** el usuario registra una merma de 0,75 kg
- **THEN** el stock queda en 4,25 kg

#### Scenario: Merma mayor al stock
- **WHEN** el usuario registra una merma mayor al stock disponible
- **THEN** el sistema la rechaza con un error y el stock no cambia

#### Scenario: Cantidad no positiva
- **WHEN** el usuario registra una merma de 0 o negativa
- **THEN** el sistema la rechaza con un error y el stock no cambia

#### Scenario: Local sin stock
- **WHEN** el stock del producto en el local es 0
- **THEN** la acción de merma está deshabilitada
