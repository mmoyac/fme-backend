## ADDED Requirements

### Requirement: Autenticación y aislamiento por tenant en solicitudes
Todos los endpoints de solicitudes de transferencia MUST exigir un usuario autenticado y operar solo sobre solicitudes, locales y productos del tenant de ese usuario. Una solicitud de otro tenant MUST responder 404 en consulta, edición y eliminación.

#### Scenario: Consulta sin token
- **WHEN** alguien consulta, crea o elimina una solicitud sin token válido
- **THEN** el sistema responde 401 y no lee ni modifica datos

#### Scenario: Solicitud de otro tenant
- **WHEN** un usuario autenticado consulta o elimina una solicitud que pertenece a otro tenant
- **THEN** el sistema responde 404

### Requirement: Datos de creación fijados por el servidor
Al crear una solicitud, el sistema SHALL fijar el tenant y el solicitante desde el usuario autenticado y el estado inicial en `PENDIENTE`, ignorando esos valores si vienen en la petición.

#### Scenario: Cliente envía otro tenant
- **WHEN** un usuario del tenant 1 crea una solicitud enviando `tenant_id` 2 y estado FINALIZADO
- **THEN** la solicitud queda en el tenant 1, en estado PENDIENTE y con el usuario como solicitante

### Requirement: Eliminación restringida
Eliminar una solicitud SHALL estar permitido solo a un admin o al usuario solicitante; otro usuario MUST recibir 403.

#### Scenario: Usuario ajeno intenta eliminar
- **WHEN** un usuario que no es admin ni el solicitante intenta eliminar la solicitud
- **THEN** el sistema responde 403 y la solicitud se mantiene
