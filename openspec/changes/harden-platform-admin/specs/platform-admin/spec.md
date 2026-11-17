## ADDED Requirements

### Requirement: Gestión de tenants restringida a la plataforma
Solo un administrador de plataforma SHALL poder listar, ver, crear, modificar, activar/desactivar o eliminar tenants y ver los usuarios de un tenant. Cualquier otro usuario autenticado SHALL recibir HTTP 403.

#### Scenario: Usuario de tenant intenta listar tenants
- **WHEN** un usuario con rol `admin` de un tenant, sin ser administrador de plataforma, llama `GET /api/tenants/`
- **THEN** el sistema responde HTTP 403

#### Scenario: Usuario de tenant intenta eliminar otro tenant
- **WHEN** un usuario de un tenant llama `DELETE /api/tenants/{id}`
- **THEN** el sistema responde HTTP 403 y el tenant no se modifica

### Requirement: Contexto de tenant del administrador de plataforma
Cuando un administrador de plataforma opera dentro de un tenant, el sistema SHALL aplicar ese tenant solo durante la request y MUST NOT modificar el tenant de origen almacenado para ese administrador.

#### Scenario: Operación con commit dentro de un tenant
- **WHEN** un administrador de plataforma, operando en el tenant 7, ejecuta una operación que confirma cambios en la BD
- **THEN** la operación usa el tenant 7 durante toda la request
- **AND** el registro del administrador conserva su tenant de origen

### Requirement: Acceso de soporte acotado y visible
El token para operar dentro de un tenant SHALL expirar a los 30 minutos, SHALL identificar al administrador que actúa, y la interfaz SHALL mostrar de forma permanente en qué tenant se está operando.

#### Scenario: Token de soporte vencido
- **WHEN** un administrador usa un token de operación en tenant emitido hace más de 30 minutos
- **THEN** el sistema responde HTTP 401

### Requirement: Bitácora de acciones de plataforma
El sistema SHALL registrar, en la misma transacción que el cambio y de forma inmutable, toda acción de plataforma: alta, modificación, eliminación, activación o desactivación de tenants, creación de administradores de plataforma, y cada entrada y salida de un tenant. Si la acción afecta a un tenant, SHALL quedar visible en la bitácora de ese tenant.

#### Scenario: Entrada a un tenant
- **WHEN** un administrador de plataforma entra al tenant "elolivo"
- **THEN** queda un registro con el administrador, el tenant, la fecha, la IP y la acción `tenants:enter`

#### Scenario: Intento de modificar la bitácora
- **WHEN** la aplicación intenta actualizar o eliminar un registro de la bitácora
- **THEN** la base de datos lo rechaza

### Requirement: Identidad de plataforma separada
Los administradores de plataforma SHALL existir separados de los usuarios de tenant, iniciar sesión solo en el host de administración y con segundo factor obligatorio. Un token de plataforma SHALL ser rechazado por la API de tenants y un token de tenant SHALL ser rechazado por la API de plataforma.

#### Scenario: Token de tenant contra la API de plataforma
- **WHEN** se usa un token de usuario de tenant contra la API de plataforma en `effichain-admin.effi4tech.cl`
- **THEN** el sistema responde HTTP 401

#### Scenario: Login de plataforma desde un dominio de tenant
- **WHEN** un administrador de plataforma intenta iniciar sesión en `effichain-elolivo-admin.effi4tech.cl`
- **THEN** el sistema rechaza el inicio de sesión

### Requirement: Aislamiento de datos en la base de datos
El aislamiento entre tenants MUST aplicarse en la base de datos, de modo que se mantenga aun ante un error en la lógica de la aplicación.

#### Scenario: Consulta sin filtro de tenant
- **WHEN** una consulta sobre una tabla de negocio se ejecuta en el contexto del tenant A sin filtrar por `tenant_id`
- **THEN** la base de datos devuelve solo filas del tenant A

#### Scenario: Consulta sin contexto de tenant
- **WHEN** una consulta sobre una tabla de negocio se ejecuta sin contexto de tenant
- **THEN** la base de datos no devuelve filas
