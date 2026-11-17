## ADDED Requirements

### Requirement: Usuario responsable en cada movimiento
Todo movimiento registrado por una acción de un usuario en el módulo de inventario (transferencia directa, merma, conteo) MUST guardar el nombre del usuario autenticado y su identificador; el historial SHALL mostrar ese nombre.

#### Scenario: Transferencia muestra al usuario real
- **GIVEN** la usuaria "María Pérez" realizó una transferencia
- **WHEN** se consulta el historial
- **THEN** el movimiento muestra "María Pérez" como usuario y no "admin"
