## ADDED Requirements

### Requirement: Conteo limitado al local propio
Un usuario con local asignado y sin alcance total SHALL poder iniciar conteos solo en su local (preseleccionado y fijo), ver solo conteos de su local y registrar cantidades, finalizar, cancelar o exportar solo conteos de su local; sobre un conteo o local ajeno el sistema MUST responder 403.

#### Scenario: Vendedor inicia conteo
- **GIVEN** un vendedor con local asignado TilTil
- **WHEN** abre "Nuevo conteo"
- **THEN** el local es TilTil y no puede elegir otro

#### Scenario: Conteo de otro local
- **WHEN** un vendedor de TilTil intenta abrir, registrar o finalizar un conteo de Lampa vía API
- **THEN** el sistema responde 403 y el conteo no cambia

#### Scenario: Lista de conteos
- **WHEN** un vendedor de TilTil abre la pestaña Conteo
- **THEN** solo ve conteos de TilTil
