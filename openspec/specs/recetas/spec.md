# Recetas Specification

## Purpose

Permite definir la **receta** de un producto elaborado: la lista de ingredientes
(otros productos), las cantidades y unidades que se consumen, y el rendimiento que
produce. A partir de la receta el sistema **calcula el costo de fabricación** del
producto y mantiene el flag de "tiene receta", de modo que producción y costeo
trabajen sobre datos consistentes.

El comportamiento descrito aquí lo expone `fme-backend` (router `recetas`,
prefijo `/api/recetas`). El backoffice (`admin.masasestacion.cl`) es un cliente
que consume estos endpoints; la lógica de negocio (versionado y costeo) vive en
el backend.

## Requirements

### Requirement: Crear receta de un producto

El sistema SHALL permitir crear una receta asociada a un producto existente,
recibiendo nombre, rendimiento, unidad de rendimiento, notas opcionales y una
lista de ingredientes. La operación requiere un usuario autenticado y activo.

#### Scenario: Crear receta con ingredientes

- **WHEN** un usuario autenticado hace `POST /api/recetas/productos/{producto_id}/receta`
  con `nombre`, `rendimiento` (> 0), `unidad_rendimiento_id` y al menos un ingrediente
- **THEN** el sistema crea la receta vinculada a `producto_id`, persiste sus ingredientes,
  calcula sus costos y responde `201 Created` con la receta y sus ingredientes

#### Scenario: Producto inexistente

- **WHEN** se intenta crear una receta para un `producto_id` que no existe
- **THEN** el sistema responde `404` con detalle "Producto no encontrado" y no crea nada

#### Scenario: Rendimiento inválido

- **WHEN** se envía `rendimiento` menor o igual a 0
- **THEN** el sistema rechaza la petición con error de validación `422`

### Requirement: Versionado por receta activa

Un producto SHALL tener como máximo una receta activa a la vez. Al crear una nueva
receta para un producto, las recetas activas anteriores de ese producto pasan a
`activa = false`, conservándose como historial.

#### Scenario: Nueva receta desactiva la anterior

- **WHEN** un producto ya tiene una receta `activa = true` y se crea una nueva receta
- **THEN** la receta anterior queda `activa = false` y la nueva queda `activa = true`

#### Scenario: Obtener la receta activa

- **WHEN** un usuario hace `GET /api/recetas/productos/{producto_id}/receta`
- **THEN** el sistema responde la receta con `activa = true` del producto, o `404`
  "Receta no encontrada" si el producto no tiene receta activa

### Requirement: Gestión de ingredientes de la receta

El sistema SHALL permitir agregar, actualizar y eliminar ingredientes de una receta
existente. Cada ingrediente referencia otro producto (`producto_ingrediente_id`),
una cantidad (> 0), una unidad de medida, un orden de visualización y notas opcionales.

#### Scenario: Agregar ingrediente a receta existente

- **WHEN** un usuario hace `POST /api/recetas/recetas/{receta_id}/ingredientes`
  con un ingrediente válido
- **THEN** el sistema agrega el ingrediente, recalcula los costos de la receta y
  responde `201 Created` con el ingrediente creado

#### Scenario: Actualizar un ingrediente

- **WHEN** un usuario hace `PUT /api/recetas/ingredientes/{ingrediente_id}` con
  campos a modificar (cantidad, unidad, producto, orden o notas)
- **THEN** el sistema actualiza el ingrediente y recalcula los costos de su receta

#### Scenario: Eliminar un ingrediente

- **WHEN** un usuario hace `DELETE /api/recetas/ingredientes/{ingrediente_id}`
- **THEN** el sistema elimina el ingrediente, recalcula los costos de la receta y
  responde `204 No Content`

### Requirement: Cálculo de costos de la receta

El sistema SHALL calcular el costo de cada ingrediente y el costo total y unitario
de la receta cada vez que la receta o sus ingredientes cambian. El costo unitario
de cada ingrediente se deriva de su precio de compra (o costo de fabricación si es
un producto elaborado), normalizado por su factor de conversión de compra, y
convertido a la unidad usada en la receta.

#### Scenario: Costo total y unitario

- **WHEN** se calculan los costos de una receta
- **THEN** cada ingrediente recibe `costo_unitario_referencia` y `costo_total_calculado`,
  la receta recibe `costo_total_calculado` (suma de los ingredientes) y
  `costo_unitario_calculado` = `costo_total_calculado / rendimiento`

#### Scenario: Conversión de unidades entre receta e ingrediente

- **WHEN** la unidad del ingrediente en la receta difiere de la unidad base del producto
- **THEN** la cantidad se convierte usando los `factor_conversion` de ambas unidades
  antes de calcular el costo

#### Scenario: Recálculo manual

- **WHEN** un usuario hace `POST /api/recetas/recetas/{receta_id}/recalcular`
- **THEN** el sistema recalcula y persiste los costos de la receta y responde con la
  receta actualizada

### Requirement: Sincronización con el producto

El sistema SHALL mantener en el producto el costo de fabricación y el indicador de
receta derivados de su receta activa.

#### Scenario: Producto refleja costo y flag al crear receta

- **WHEN** se crea una receta para un producto y se calculan sus costos
- **THEN** `producto.costo_fabricacion` toma el `costo_unitario_calculado` de la receta
  y `producto.tiene_receta` se marca como `true`

#### Scenario: Eliminar receta actualiza el producto

- **WHEN** un usuario hace `DELETE /api/recetas/recetas/{receta_id}`
- **THEN** el sistema elimina la receta, responde `204 No Content` y actualiza
  `producto.tiene_receta` según queden o no recetas; si no queda ninguna,
  `producto.costo_fabricacion` se deja en `null`

### Requirement: Restricciones de composición

El sistema SHALL impedir que un producto se use como ingrediente de su propia receta.

#### Scenario: Producto no es ingrediente de sí mismo

- **WHEN** se construye la receta de un producto
- **THEN** el propio producto no está disponible como ingrediente seleccionable
