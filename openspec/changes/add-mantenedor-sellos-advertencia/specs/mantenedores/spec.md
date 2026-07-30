## ADDED Requirements

### Requirement: Mantenedor de Sellos de Advertencia

El módulo de Mantenedores SHALL incluir un mantenedor de **Sellos de Advertencia** **embebido en la grilla de `/admin/mantenedores`** (no como página dedicada), que administra el catálogo global `sellos_advertencia` reusando el patrón CRUD compartido. Este mantenedor SHALL ser una tabla maestra **global** (sin alcance por tenant).

Campos administrables por sello: `codigo`, `nombre`, `descripcion`, `color`, `icono`, `orden`, `activo`.

#### Scenario: Acceder al mantenedor desde la grilla

- **WHEN** un administrador abre `/admin/mantenedores` y selecciona la opción "Sellos de Advertencia"
- **THEN** el sistema muestra el CRUD de sellos embebido dentro del mismo módulo (no redirige a otra página)

#### Scenario: Crear un sello

- **WHEN** el administrador crea un sello con un `codigo` que no existe
- **THEN** el sistema agrega el sello al catálogo y responde con el registro creado

#### Scenario: Editar un sello

- **WHEN** el administrador edita los campos presentacionales de un sello (nombre, descripción, color, icono, orden, activo)
- **THEN** el sistema actualiza el sello

#### Scenario: Deshabilitar un sello

- **WHEN** el administrador establece `activo = false` en un sello
- **THEN** el sello deja de aparecer en el selector de sellos de los productos pero permanece en el catálogo

### Requirement: Sellos de sistema protegidos

Los 6 sellos base provistos por el seed (ALTO_CALORIAS, ALTO_AZUCARES, ALTO_SODIO, ALTO_GRASAS_SAT, CONTIENE_EDULCORANTES, CONTIENE_CAFEINA) SHALL tratarse como registros de sistema y NO SHALL poder eliminarse. Su `codigo` no SHALL modificarse; sí se permiten cambios presentacionales.

#### Scenario: Intentar eliminar un sello de sistema

- **WHEN** el administrador intenta eliminar uno de los 6 sellos base
- **THEN** el sistema rechaza la operación y el sello permanece

### Requirement: Borrado de sello protegido por asignación a productos

El sistema NO SHALL permitir eliminar un sello que esté asignado a uno o más productos (`producto_sellos`). Para retirarlo de circulación se usa `activo = false`.

#### Scenario: Eliminar sello asignado a productos

- **WHEN** el administrador intenta eliminar un sello que está asignado a al menos un producto
- **THEN** el sistema rechaza la operación con un error de solicitud (400) indicando que está en uso

#### Scenario: Eliminar sello sin asignaciones

- **WHEN** el administrador elimina un sello no-sistema que no está asignado a ningún producto
- **THEN** el sistema elimina el sello del catálogo
