## ADDED Requirements

### Requirement: Cantidad como factor de alta precisión

La `cantidad` de un ingrediente SHALL interpretarse como un factor (multiplicador) y
SHALL almacenarse con hasta 8 decimales, sin truncar la precisión que ingresa el
usuario, de modo que el costo calculado coincida con el modelo de costeo del cliente.

#### Scenario: Cantidad con muchos decimales

- **WHEN** se envía un ingrediente con una `cantidad` de hasta 8 decimales
  (por ejemplo `2.71000000` o `0.05743210`)
- **THEN** el sistema persiste la cantidad con esa precisión y la usa íntegra en el
  cálculo de costos, sin redondearla a 3 decimales

### Requirement: Sin ingredientes duplicados

El sistema SHALL impedir que un mismo producto aparezca más de una vez como ingrediente
de una receta, tanto al crear la receta como al agregar ingredientes posteriormente.

#### Scenario: Agregar un producto ya presente

- **WHEN** se intenta agregar a una receta un ingrediente cuyo `producto_ingrediente_id`
  ya existe en esa receta
- **THEN** el sistema lo rechaza con `400` y un mensaje claro, sin duplicar el ingrediente

#### Scenario: Crear receta con productos repetidos

- **WHEN** se crea una receta cuya lista de ingredientes contiene el mismo
  `producto_ingrediente_id` más de una vez
- **THEN** el sistema rechaza la creación con `400` y no crea la receta

### Requirement: Validación de límites numéricos

El sistema SHALL validar que los valores numéricos de entrada y los costos derivados
caben en la precisión soportada por el almacenamiento (`cantidad` con escala 8 y máximo
10 dígitos enteros; costos con escala 2 y máximo 8 dígitos enteros) antes de persistir,
rechazando con un error claro los valores fuera de rango en lugar de fallar en el commit.

#### Scenario: Valor numérico fuera de rango

- **WHEN** una `cantidad` o un costo calculado excede el máximo representable por su
  columna (parte entera mayor a la soportada)
- **THEN** el sistema responde un error de validación (`400`/`422`) con un mensaje
  claro, y no deja datos a medias

## MODIFIED Requirements

### Requirement: Crear receta de un producto

El sistema SHALL permitir crear una receta asociada a un producto existente,
recibiendo nombre, rendimiento, unidad de rendimiento, notas opcionales y una
lista de ingredientes. La operación requiere un usuario autenticado y activo, y
SHALL ser atómica: la receta, sus ingredientes, los costos calculados y el flag
`producto.tiene_receta` se persisten en una sola transacción; ante cualquier error
se hace `rollback` y no queda ninguna receta parcial.

#### Scenario: Crear receta con ingredientes

- **WHEN** un usuario autenticado hace `POST /api/recetas/productos/{producto_id}/receta`
  con `nombre`, `rendimiento` (> 0), `unidad_rendimiento_id` y al menos un ingrediente
- **THEN** el sistema crea la receta vinculada a `producto_id`, persiste sus ingredientes,
  calcula sus costos, marca `producto.tiene_receta = true` y responde `201 Created`
  con la receta y sus ingredientes

#### Scenario: Producto inexistente

- **WHEN** se intenta crear una receta para un `producto_id` que no existe
- **THEN** el sistema responde `404` con detalle "Producto no encontrado" y no crea nada

#### Scenario: Rendimiento inválido

- **WHEN** se envía `rendimiento` menor o igual a 0
- **THEN** el sistema rechaza la petición con error de validación `422`

#### Scenario: Fallo durante el cálculo de costos

- **WHEN** ocurre un error al crear la receta (por ejemplo, al calcular los costos)
- **THEN** el sistema hace `rollback` de toda la operación y no deja una receta sin
  costos ni un `producto.tiene_receta` inconsistente

### Requirement: Gestión de ingredientes de la receta

El sistema SHALL permitir agregar, actualizar y eliminar ingredientes de una receta
existente. Cada ingrediente referencia otro producto (`producto_ingrediente_id`),
una cantidad (> 0), una unidad de medida, un orden de visualización y notas opcionales.
Cada una de estas operaciones SHALL ser atómica: el cambio del ingrediente y el
recálculo de costos de la receta se confirman juntos, y ante un error se hace
`rollback` sin dejar la receta en estado inconsistente.

#### Scenario: Agregar ingrediente a receta existente

- **WHEN** un usuario hace `POST /api/recetas/recetas/{receta_id}/ingredientes`
  con un ingrediente válido
- **THEN** el sistema agrega el ingrediente, recalcula los costos de la receta en la
  misma transacción y responde `201 Created` con el ingrediente creado

#### Scenario: Actualizar un ingrediente

- **WHEN** un usuario hace `PUT /api/recetas/ingredientes/{ingrediente_id}` con
  campos a modificar (cantidad, unidad, producto, orden o notas)
- **THEN** el sistema actualiza el ingrediente y recalcula los costos de su receta

#### Scenario: Eliminar un ingrediente

- **WHEN** un usuario hace `DELETE /api/recetas/ingredientes/{ingrediente_id}`
- **THEN** el sistema elimina el ingrediente, recalcula los costos de la receta y
  responde `204 No Content`

#### Scenario: Fallo al recalcular costos

- **WHEN** falla el recálculo de costos al agregar/editar/eliminar un ingrediente
- **THEN** el sistema hace `rollback` de la operación completa y la receta conserva
  su estado previo consistente

### Requirement: Cálculo de costos de la receta

El sistema SHALL calcular el costo de cada ingrediente y el costo total y unitario
de la receta cada vez que la receta o sus ingredientes cambian. El costo unitario
de cada ingrediente se deriva de su precio de compra (o costo de fabricación si es
un producto elaborado), normalizado por su factor de conversión de compra, y
convertido a la unidad usada en la receta. Todos los valores que se persistan SHALL
redondearse (`quantize`) a la escala de su columna (2 decimales para costos) antes de
guardarse, y el cálculo SHALL evitar producir valores que excedan la precisión de la
columna.

#### Scenario: Costo total y unitario

- **WHEN** se calculan los costos de una receta
- **THEN** cada ingrediente recibe `costo_unitario_referencia` y `costo_total_calculado`
  redondeados a 2 decimales, la receta recibe `costo_total_calculado` (suma de los
  ingredientes) y `costo_unitario_calculado` = `costo_total_calculado / rendimiento`,
  ambos redondeados a 2 decimales

#### Scenario: Conversión de unidades entre receta e ingrediente

- **WHEN** la unidad del ingrediente en la receta difiere de la unidad base del producto
- **THEN** la cantidad se convierte usando los `factor_conversion` de ambas unidades
  antes de calcular el costo

#### Scenario: Recálculo manual

- **WHEN** un usuario hace `POST /api/recetas/recetas/{receta_id}/recalcular`
- **THEN** el sistema recalcula y persiste los costos de la receta y responde con la
  receta actualizada

#### Scenario: Costo de alta precisión no provoca overflow

- **WHEN** una división del cálculo produce un `Decimal` de alta precisión
- **THEN** el valor se redondea a la escala de la columna antes de persistir y la
  operación no falla por `numeric field overflow`
