## ADDED Requirements

### Requirement: Listado de registros de una tabla maestra

Cada mantenedor SHALL exponer un endpoint de listado que devuelve los registros de su tabla maestra. El listado SHALL aceptar un filtro opcional por bandera `activo` y, cuando aplique, paginación (`skip`/`limit`).

#### Scenario: Listar todos los registros

- **WHEN** un usuario autenticado solicita el listado de un mantenedor sin filtros
- **THEN** el sistema devuelve todos los registros de esa tabla maestra

#### Scenario: Filtrar por estado activo

- **WHEN** un usuario autenticado solicita el listado con `activo=true`
- **THEN** el sistema devuelve únicamente los registros con `activo = true`

### Requirement: Obtener un registro por id

Cada mantenedor SHALL exponer un endpoint para obtener un registro individual por su `id`.

#### Scenario: Registro existente

- **WHEN** se solicita un registro por un `id` que existe
- **THEN** el sistema devuelve el registro

#### Scenario: Registro inexistente

- **WHEN** se solicita un registro por un `id` que no existe
- **THEN** el sistema responde `404 Not Found`

### Requirement: Crear un registro con código único

Cada mantenedor que tenga campo `codigo` SHALL validar que el código sea único antes de crear el registro. La creación SHALL rechazarse si el código ya existe.

#### Scenario: Creación válida

- **WHEN** se crea un registro con un código que no existe
- **THEN** el sistema crea el registro y responde `201 Created` con el registro creado

#### Scenario: Código duplicado

- **WHEN** se intenta crear un registro con un código que ya existe
- **THEN** el sistema rechaza la operación con un error de solicitud (400) indicando que el código ya existe

### Requirement: Actualizar un registro (parcial) con código único

Cada mantenedor SHALL permitir actualización parcial de un registro (solo los campos enviados se modifican). Si se cambia el `codigo`, SHALL revalidarse su unicidad.

#### Scenario: Actualización parcial válida

- **WHEN** se actualiza un registro existente enviando solo algunos campos
- **THEN** el sistema modifica únicamente esos campos y conserva el resto

#### Scenario: Actualización a un código ya usado

- **WHEN** se actualiza el código de un registro a uno que ya pertenece a otro registro
- **THEN** el sistema rechaza la operación con un error de solicitud (400)

### Requirement: Eliminación protegida por uso

Cada mantenedor SHALL bloquear la eliminación de un registro que esté referenciado por otras entidades. Si el registro no tiene referencias, la eliminación SHALL proceder.

#### Scenario: Eliminar registro sin referencias

- **WHEN** se elimina un registro que no tiene entidades asociadas
- **THEN** el sistema elimina el registro y responde `204 No Content`

#### Scenario: Eliminar registro en uso

- **WHEN** se intenta eliminar un registro que tiene entidades asociadas (ej. una categoría con productos)
- **THEN** el sistema rechaza la operación con un error de solicitud (400) indicando que está en uso

### Requirement: Registros de sistema protegidos

Los mantenedores que contengan registros de sistema (semilla) SHALL impedir su eliminación, independientemente de si están en uso. Ejemplo: los 4 canales de venta base (POS, LANDING, WHATSAPP, TELEFONO).

#### Scenario: Intentar eliminar un registro de sistema

- **WHEN** se intenta eliminar un registro marcado como de sistema (ej. el canal POS)
- **THEN** el sistema rechaza la operación y el registro permanece

### Requirement: Habilitar/deshabilitar mediante bandera activo

Cada mantenedor con campo `activo` SHALL permitir habilitar o deshabilitar un registro sin eliminarlo, cambiando la bandera `activo`. Los registros inactivos SHALL poder excluirse de los listados filtrados y de los selectores de otras pantallas.

#### Scenario: Deshabilitar un registro

- **WHEN** se actualiza un registro estableciendo `activo = false`
- **THEN** el registro permanece en la base de datos pero queda marcado como inactivo

### Requirement: Autorización de lectura y escritura

Las operaciones de lectura (listar/obtener) de los mantenedores SHALL requerir un usuario autenticado activo. Las operaciones de escritura (crear/actualizar/eliminar) SHALL requerir el nivel de autorización definido por cada mantenedor: rol administrador donde el mantenedor lo exige, o usuario activo en los mantenedores que no elevan el requisito.

#### Scenario: Lectura sin autenticación

- **WHEN** un cliente sin sesión válida solicita listar un mantenedor
- **THEN** el sistema rechaza la solicitud (401/403)

#### Scenario: Escritura sin rol suficiente

- **WHEN** un usuario sin el rol requerido intenta crear/actualizar/eliminar en un mantenedor que exige rol administrador
- **THEN** el sistema rechaza la operación (403)

### Requirement: Alcance de datos global o por tenant

Cada mantenedor SHALL declarar su alcance de datos. Los mantenedores de **tabla maestra global** (ej. categorías, tipos de producto, unidades) comparten registros entre todos los tenants. Los mantenedores **por tenant** SHALL aislar los registros según el tenant del usuario.

#### Scenario: Mantenedor global

- **WHEN** dos usuarios de tenants distintos listan un mantenedor global
- **THEN** ambos ven el mismo conjunto de registros

#### Scenario: Mantenedor por tenant

- **WHEN** un usuario lista un mantenedor con alcance por tenant
- **THEN** el sistema devuelve únicamente los registros de su tenant

### Requirement: Inventario de mantenedores del módulo

El módulo de Mantenedores (`/admin/mantenedores`) SHALL exponer, como fuente de verdad de la UI, el conjunto de mantenedores disponibles. Al agregar un mantenedor nuevo, este inventario SHALL actualizarse en el mismo change.

Inventario base (estado documentado):

- **CRUD embebidos en el módulo**: Ubicaciones, Estados de Enrolamiento, Tipos de Vehículo, Paleta de Colores, Tipos de Venta, Categorías, Tipos de Producto, Unidades de Medida, Locales, Proveedores, Tipos de Proveedor, Tipos de Documento, Tipos de Pedido, Medios de Pago, Estados de Cheque, Bancos, Canales de Venta, Tipos de OT, Etapas de OT, Roles y Permisos.
- **Opciones que redirigen a páginas dedicadas** (fuera del alcance del patrón CRUD embebido): Config. Landing (`/admin/configuracion/landing`), Usuarios (`/admin/usuarios`), Tenants (`/admin/tenants`).

#### Scenario: Acceder al módulo

- **WHEN** un administrador abre `/admin/mantenedores`
- **THEN** el sistema muestra la grilla con las opciones del inventario, cada una llevando a su CRUD embebido o a su página dedicada

#### Scenario: Agregar un mantenedor nuevo

- **WHEN** se agrega un mantenedor nuevo mediante un change de OpenSpec
- **THEN** el change actualiza este inventario e implementa el patrón CRUD compartido definido en esta spec
