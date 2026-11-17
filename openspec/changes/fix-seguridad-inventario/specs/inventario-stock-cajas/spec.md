## ADDED Requirements

### Requirement: Aislamiento por tenant en escrituras de cajas
El ajuste manual, la actualización desde enrolamiento y la validación de reserva de cajas MUST operar solo sobre productos del tenant del usuario autenticado; un producto de otro tenant MUST responder 404 sin modificar el contador.

#### Scenario: Ajuste sobre producto de otro tenant
- **WHEN** un usuario intenta ajustar las cajas de un producto que pertenece a otro tenant
- **THEN** el sistema responde 404 y el contador no cambia
