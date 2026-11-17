## ADDED Requirements

### Requirement: Alcance por local en Existencias
Un usuario con alcance total (superadmin, rol admin o sin local asignado) SHALL ver en Existencias un selector de local con la opción "Todos los locales" y cada local activo, visible solo si el tenant tiene más de un local físico (sin contar WEB). Un usuario con local asignado y sin rol admin SHALL ver solo el stock de su local, sin selector y sin el consolidado WEB, y MUST NOT poder registrar merma en otro local: el backend responde 403.

#### Scenario: Admin con varios locales
- **GIVEN** un admin y un tenant con Lampa, TilTil y boulevard
- **WHEN** abre Existencias
- **THEN** ve el selector con "Todos los locales" seleccionado y el stock de todos los locales

#### Scenario: Admin filtra un local
- **WHEN** el admin elige "TilTil" en el selector
- **THEN** cada producto muestra solo el stock de TilTil

#### Scenario: Tenant con un solo local
- **GIVEN** un tenant con un único local físico
- **WHEN** un admin abre Existencias
- **THEN** no se muestra el selector

#### Scenario: Vendedor de tienda
- **GIVEN** un vendedor con local asignado TilTil
- **WHEN** abre Existencias
- **THEN** ve solo el stock de TilTil, sin selector ni fila WEB

#### Scenario: Merma en otro local
- **WHEN** un vendedor de TilTil intenta registrar merma en Lampa vía API
- **THEN** el sistema responde 403 y el stock no cambia
