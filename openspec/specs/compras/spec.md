# Compras Specification

## Purpose

Gestiona el **abastecimiento de mercadería**: el registro de **proveedores** y el
flujo de **órdenes de compra** con estados, que al recibirse impactan el inventario
del local destino y actualizan el precio de compra de los productos.

El objetivo es separar el "registro de la compra" del "ingreso a stock": una compra
se crea como **PENDIENTE** (sin afectar inventario, totalmente editable) y solo al
**recibirla** suma cantidades al inventario y recalcula costos, quedando inmutable.

El comportamiento descrito aquí lo expone `fme-backend` (router `compras`, prefijo
`/api/compras`). El backoffice (`admin.masasestacion.cl/admin/compras`) es un cliente
que consume estos endpoints; la lógica de negocio (estados, costeo e impacto en
inventario) vive en el backend. Todas las operaciones requieren un usuario
autenticado y activo, y están aisladas por `tenant_id`.

## Requirements

### Requirement: Aislamiento por tenant

El sistema SHALL exponer únicamente los proveedores y compras pertenecientes al
`tenant_id` del usuario autenticado. Las compras se filtran por el `tenant_id` del
local asociado; los proveedores por su propio `tenant_id`.

#### Scenario: Acceso a compra de otro tenant

- **WHEN** un usuario solicita una compra cuyo local pertenece a otro tenant
- **THEN** el sistema responde `404` "Compra no encontrada" y no expone datos

#### Scenario: Creación valida el local

- **WHEN** un usuario crea una compra con un `local_id` que no pertenece a su tenant
- **THEN** el sistema responde `404` "Local no encontrado o no pertenece a tu organización" y no crea nada

### Requirement: Gestión de proveedores

El sistema SHALL permitir listar, crear y actualizar proveedores. Un proveedor tiene
`nombre` (requerido), y opcionalmente `rut`, `contacto`, `email`, `telefono`,
`direccion`, `tipo_proveedor_id` y `activo`. El `rut` SHALL ser único por tenant.

#### Scenario: Listar proveedores

- **WHEN** un usuario hace `GET /api/compras/proveedores`
- **THEN** el sistema responde la lista de proveedores del tenant ordenada por `nombre`,
  cada uno con su `tipo_proveedor` asociado

#### Scenario: Crear proveedor

- **WHEN** un usuario hace `POST /api/compras/proveedores` con al menos `nombre`
- **THEN** el sistema crea el proveedor en el tenant del usuario y responde con el proveedor creado

#### Scenario: RUT duplicado en el tenant

- **WHEN** se intenta crear un proveedor con un `rut` ya registrado en el mismo tenant
- **THEN** el sistema responde `400` con detalle indicando que el RUT ya está registrado y no crea nada

#### Scenario: Actualizar proveedor

- **WHEN** un usuario hace `PUT /api/compras/proveedores/{proveedor_id}` con campos a modificar
- **THEN** el sistema actualiza solo los campos enviados; si el proveedor no existe en el tenant responde `404` "Proveedor no encontrado"

### Requirement: Crear orden de compra en estado PENDIENTE

El sistema SHALL permitir crear una compra recibiendo cabecera (`proveedor_id`,
`local_id`, `tipo_documento_id`, `fecha_compra` opcional, `numero_documento` opcional,
`notas` opcional) y una lista de `detalles` (cada uno con `producto_id`, `cantidad` y
`precio_unitario`). La compra se crea en estado **PENDIENTE** y **NO afecta el inventario**.

#### Scenario: Crear compra pendiente

- **WHEN** un usuario hace `POST /api/compras/` con cabecera válida y al menos un detalle
- **THEN** el sistema crea la compra en estado `PENDIENTE`, persiste sus detalles,
  calcula `monto_total` y responde con la compra; el inventario no cambia

#### Scenario: Cálculo del monto total

- **WHEN** se crea o actualiza una compra
- **THEN** `monto_total` = suma de (`cantidad` × `precio_unitario`) de todos los detalles

#### Scenario: Fecha por defecto

- **WHEN** se crea una compra sin `fecha_compra`
- **THEN** el sistema usa la fecha y hora actuales. Se acepta el formato `YYYY-MM-DD`

### Requirement: Listar y consultar compras

El sistema SHALL permitir listar las compras del tenant y consultar una compra por id,
incluyendo sus detalles.

#### Scenario: Listar compras

- **WHEN** un usuario hace `GET /api/compras/`
- **THEN** el sistema responde las compras del tenant ordenadas por `id` descendente (las nuevas primero)

#### Scenario: Consultar una compra

- **WHEN** un usuario hace `GET /api/compras/{compra_id}` de una compra de su tenant
- **THEN** el sistema responde la compra con su cabecera, `estado`, `monto_total` y `detalles`

### Requirement: Editar compra solo si está pendiente

El sistema SHALL permitir actualizar una compra **solo si su estado es PENDIENTE**.
La actualización reemplaza la cabecera y **sustituye por completo** los detalles
anteriores por los nuevos, recalculando `monto_total`.

#### Scenario: Editar compra pendiente

- **WHEN** un usuario hace `PUT /api/compras/{compra_id}` sobre una compra `PENDIENTE`
- **THEN** el sistema actualiza la cabecera, elimina los detalles previos, crea los nuevos
  y recalcula `monto_total`

#### Scenario: Intentar editar compra recibida

- **WHEN** un usuario hace `PUT /api/compras/{compra_id}` sobre una compra `RECIBIDA`
- **THEN** el sistema responde `400` "No se puede modificar una compra ya recibida" y no cambia nada

### Requirement: Recibir compra e impactar inventario

El sistema SHALL permitir transicionar una compra de `PENDIENTE` a **RECIBIDA**
mediante `POST /api/compras/{compra_id}/recibir`. Al recibir, por cada detalle el
sistema suma la cantidad al inventario del local destino (creando el registro de
inventario si no existe) y actualiza el `precio_compra` del producto. Una compra
recibida es inmutable.

#### Scenario: Recibir compra

- **WHEN** un usuario hace `POST /api/compras/{compra_id}/recibir` sobre una compra `PENDIENTE`
- **THEN** el sistema marca la compra como `RECIBIDA`, suma las cantidades al inventario
  del `local_id` y actualiza el `precio_compra` de cada producto

#### Scenario: Factor de conversión de compra

- **WHEN** un producto tiene `factor_conversion_compra` (ej. se compra en sacos de 25 kg)
- **THEN** la cantidad ingresada al inventario es `cantidad × factor_conversion_compra`
  y el `precio_compra` registrado es `precio_unitario / factor_conversion_compra`
  (precio por unidad de inventario)

#### Scenario: Inventario inexistente

- **WHEN** no existe registro de inventario para el `producto_id` y `local_id` de la compra
- **THEN** el sistema crea el registro con stock inicial 0 antes de sumar la cantidad recibida

#### Scenario: Compra ya recibida

- **WHEN** se intenta recibir una compra que ya está `RECIBIDA`
- **THEN** el sistema responde `400` "La compra ya fue recibida" y no vuelve a impactar el inventario

### Requirement: Eliminar compra

El sistema SHALL permitir eliminar una compra. Por defecto **no permite eliminar
compras RECIBIDAS** (que ya afectaron stock); puede forzarse con `force=true` para
resets completos. Al eliminar una compra se eliminan sus detalles en cascada.

#### Scenario: Eliminar compra pendiente

- **WHEN** un usuario hace `DELETE /api/compras/{compra_id}` sobre una compra `PENDIENTE`
- **THEN** el sistema elimina la compra y sus detalles y responde `204 No Content`

#### Scenario: Eliminar compra recibida sin forzar

- **WHEN** un usuario hace `DELETE /api/compras/{compra_id}` sobre una compra `RECIBIDA` sin `force`
- **THEN** el sistema responde `400` indicando que no se puede eliminar una compra ya recibida y no elimina nada

#### Scenario: Eliminar compra recibida forzando

- **WHEN** un usuario hace `DELETE /api/compras/{compra_id}?force=true` sobre una compra `RECIBIDA`
- **THEN** el sistema elimina la compra y sus detalles y responde `204 No Content`. La eliminación
  no revierte el stock previamente sumado

### Requirement: Tipo de documento tributario referenciado

El sistema SHALL exigir un `tipo_documento_id` que referencia la entidad
`tipos_documento_tributario` (factura, boleta, guía, etc.). El número del documento
(`numero_documento`) es texto libre opcional.

#### Scenario: Compra con tipo de documento

- **WHEN** se crea una compra con un `tipo_documento_id` válido
- **THEN** el sistema persiste la referencia al tipo de documento y la expone al consultar la compra
