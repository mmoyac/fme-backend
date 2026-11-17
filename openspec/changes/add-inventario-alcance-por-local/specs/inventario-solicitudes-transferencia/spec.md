## ADDED Requirements

### Requirement: Stock del local origen al solicitar
Al crear o editar una solicitud, el formulario SHALL mostrar el stock disponible de cada producto en el local origen elegido, también para usuarios que solo tienen acceso a su propio local en Existencias.

#### Scenario: Vendedor elige a quién pedir
- **GIVEN** un vendedor de TilTil sin acceso a Existencias de Lampa
- **WHEN** arma una solicitud a Lampa con un producto
- **THEN** el formulario muestra el stock de ese producto en Lampa
