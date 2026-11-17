## ADDED Requirements

### Requirement: Transferir solo desde el local propio
Un usuario con local asignado y sin alcance total SHALL poder transferir solo desde su local (el origen queda fijo en su local) hacia cualquier otro local del tenant; una transferencia con otro origen MUST rechazarse con 403. Un usuario con alcance total puede elegir cualquier origen.

#### Scenario: Vendedor transfiere desde su local
- **GIVEN** un vendedor con local asignado Lampa
- **WHEN** abre Transferencias
- **THEN** el local de origen es Lampa y no puede cambiarlo

#### Scenario: Origen ajeno vía API
- **WHEN** un vendedor de Lampa intenta transferir desde TilTil vía API
- **THEN** el sistema responde 403 y ningún stock cambia
