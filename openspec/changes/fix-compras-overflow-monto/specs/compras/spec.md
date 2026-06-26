## MODIFIED Requirements

### Requirement: Crear orden de compra en estado PENDIENTE

El sistema SHALL permitir crear una compra recibiendo cabecera (`proveedor_id`,
`local_id`, `tipo_documento_id`, `fecha_compra` opcional, `numero_documento` opcional,
`notas` opcional) y una lista de `detalles` (cada uno con `producto_id`, `cantidad` y
`precio_unitario`). La compra se crea en estado **PENDIENTE** y **NO afecta el inventario**.
El `monto_total` resultante SHALL poder representar montos de al menos
`9.999.999.999,99` (precisión `Numeric(12, 2)`); de igual forma `precio_unitario`
de cada detalle. Si la persistencia falla (overflow numérico, llave foránea inválida
u otro error de integridad), el sistema SHALL responder un error controlado con
mensaje legible y NO un error interno genérico (`500`).

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

#### Scenario: Compra de monto alto

- **WHEN** un usuario crea una compra cuyo `monto_total` supera `99.999.999,99`
  pero no excede `9.999.999.999,99`
- **THEN** el sistema persiste la compra correctamente sin error de overflow

#### Scenario: Error de persistencia reportado de forma legible

- **WHEN** la creación de la compra falla en la base de datos (overflow numérico,
  llave foránea inválida u otro error de integridad)
- **THEN** el sistema responde un error `400` con un detalle legible que describe el
  problema, y no un `500` "Error interno del servidor"

### Requirement: Recibir compra e impactar inventario

El sistema SHALL permitir transicionar una compra de `PENDIENTE` a **RECIBIDA**
mediante `POST /api/compras/{compra_id}/recibir`. Al recibir, por cada detalle el
sistema suma la cantidad al inventario del local destino (creando el registro de
inventario si no existe) y actualiza el `precio_compra` del producto. El campo
`precio_compra` del producto SHALL poder representar valores con precisión
`Numeric(12, 2)`. Una compra recibida es inmutable. Si la persistencia falla durante
la recepción, el sistema SHALL responder un error controlado con mensaje legible y
NO un `500` genérico.

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

#### Scenario: Error de persistencia al recibir reportado de forma legible

- **WHEN** la recepción de la compra falla en la base de datos (overflow numérico u
  otro error de integridad)
- **THEN** el sistema responde un error `400` con un detalle legible y no un `500`
  genérico
