# Spec Delta

## Purpose

Permite contar físicamente el inventario de un local, completo o parcial, ajustar el stock del sistema automáticamente según lo contado y dejar un registro de auditoría inmutable de quién contó, cuándo y qué diferencias se encontraron.

## ADDED Requirements

### Requirement: Iniciar conteo por local
El sistema SHALL permitir a un usuario autenticado iniciar un conteo para un local de su tenant, indicando tipo `COMPLETO` o `PARCIAL` y una observación opcional. El conteo nace en estado `EN_PROCESO` y registra el usuario creador y la fecha de inicio.

#### Scenario: Conteo completo precarga productos
- **WHEN** el usuario inicia un conteo `COMPLETO` para el local "Punta Picana"
- **THEN** el conteo se crea en `EN_PROCESO` con una línea por cada producto activo que tenga registro de inventario en ese local, sin cantidad contada

#### Scenario: Conteo parcial nace vacío
- **WHEN** el usuario inicia un conteo `PARCIAL`
- **THEN** el conteo se crea en `EN_PROCESO` sin líneas

#### Scenario: Local de otro tenant
- **WHEN** el usuario intenta iniciar un conteo para un local que no pertenece a su tenant
- **THEN** el sistema responde 404 y no crea el conteo

### Requirement: Un solo conteo abierto por local
El sistema SHALL impedir que exista más de un conteo `EN_PROCESO` para el mismo local.

#### Scenario: Ya existe un conteo abierto
- **WHEN** el usuario intenta iniciar un conteo en un local que ya tiene un conteo `EN_PROCESO`
- **THEN** el sistema responde 409 indicando el conteo abierto existente

### Requirement: Agregar productos a un conteo parcial
El sistema SHALL permitir agregar productos del tenant a un conteo `EN_PROCESO`, individualmente o en bloque por categoría, sin duplicar productos ya presentes en el conteo.

#### Scenario: Agregar por categoría
- **WHEN** el usuario agrega la categoría "Quesos" a un conteo parcial
- **THEN** se crean líneas para los productos activos de esa categoría que aún no estaban en el conteo

#### Scenario: Producto repetido
- **WHEN** el usuario agrega un producto que ya tiene línea en el conteo
- **THEN** el sistema no crea una línea duplicada

### Requirement: Registrar cantidad contada
El sistema SHALL permitir registrar o corregir la cantidad contada de una línea mientras el conteo esté `EN_PROCESO`. Al registrarla, el sistema MUST guardar el stock del sistema en ese momento, la diferencia (contado − sistema), el usuario que capturó y la fecha de captura. La cantidad contada MUST ser ≥ 0.

#### Scenario: Captura con diferencia
- **GIVEN** el stock del sistema del producto en el local es 12
- **WHEN** el usuario registra cantidad contada 10
- **THEN** la línea guarda stock_sistema 12, contado 10, diferencia −2, el usuario y la fecha de captura

#### Scenario: Cantidad negativa
- **WHEN** el usuario registra una cantidad contada menor a 0
- **THEN** el sistema responde 400 y no modifica la línea

#### Scenario: Corrección de una captura
- **WHEN** el usuario vuelve a registrar la cantidad de una línea ya contada
- **THEN** la línea se actualiza con el nuevo contado, el stock del sistema actual, la nueva diferencia, el usuario y la fecha de esta última captura

### Requirement: Finalizar conteo ajusta stock automáticamente
Al finalizar un conteo `EN_PROCESO`, el sistema SHALL, en una sola transacción, aplicar a cada línea contada con diferencia ≠ 0 un ajuste igual a la diferencia sobre el stock actual del local, registrar un movimiento de inventario tipo `AJUSTE_CONTEO` por línea ajustada (con referencia al conteo y al usuario) y marcar el conteo `FINALIZADO` con usuario y fecha de finalización.

#### Scenario: Ajuste aplicado
- **GIVEN** una línea con stock_sistema 12, contado 10 y el stock actual del local es 12
- **WHEN** el usuario finaliza el conteo
- **THEN** el stock queda en 10 y existe un movimiento `AJUSTE_CONTEO` de −2 que referencia el conteo y el usuario

#### Scenario: Ventas ocurridas después de contar
- **GIVEN** una línea capturada con stock_sistema 12 y contado 10, y luego se vendieron 3 unidades (stock actual 9)
- **WHEN** el usuario finaliza el conteo
- **THEN** el stock queda en 7 (9 + (−2)), preservando las ventas posteriores a la captura

#### Scenario: Líneas sin diferencia o sin contar
- **WHEN** el usuario finaliza un conteo con líneas de diferencia 0 o sin cantidad contada
- **THEN** esas líneas no modifican stock ni generan movimientos; las no contadas quedan marcadas como "no contadas" en el registro

#### Scenario: Conteo sin ninguna línea contada
- **WHEN** el usuario intenta finalizar un conteo sin ninguna línea con cantidad contada
- **THEN** el sistema responde 400 y el conteo sigue `EN_PROCESO`

#### Scenario: Falla parcial
- **WHEN** ocurre un error al ajustar cualquiera de las líneas
- **THEN** no se aplica ningún ajuste y el conteo sigue `EN_PROCESO`

### Requirement: Cancelar conteo
El sistema SHALL permitir cancelar un conteo `EN_PROCESO`, registrando usuario y fecha, sin modificar el stock.

#### Scenario: Cancelación
- **WHEN** el usuario cancela un conteo `EN_PROCESO`
- **THEN** el conteo pasa a `CANCELADO` y ningún stock cambia

### Requirement: Conteo cerrado es inmutable
Un conteo `FINALIZADO` o `CANCELADO` MUST NOT poder modificarse: no se agregan líneas, no se cambian cantidades y no se puede finalizar ni cancelar de nuevo.

#### Scenario: Editar conteo finalizado
- **WHEN** el usuario intenta registrar una cantidad en un conteo `FINALIZADO`
- **THEN** el sistema responde 409 y no modifica el conteo

### Requirement: Consultar historial de conteos
El sistema SHALL listar los conteos del tenant con filtros por local, estado, rango de fechas y usuario, mostrando tipo, usuarios (creador y finalizador), fechas, cantidad de líneas contadas y cantidad de líneas con diferencia. El detalle de un conteo MUST mostrar cada línea con producto, stock sistema, contado, diferencia, usuario y fecha de captura.

#### Scenario: Filtrar por local
- **WHEN** el usuario lista conteos filtrando por el local "Punta Picana"
- **THEN** solo se devuelven conteos de ese local y del tenant del usuario

### Requirement: Exportar conteo a Excel
El sistema SHALL permitir descargar el detalle de un conteo como archivo `.xlsx` con encabezado (local, tipo, estado, usuarios, fechas) y una fila por línea con SKU, producto, categoría, unidad, stock sistema, contado, diferencia, usuario y fecha de captura.

#### Scenario: Descarga de conteo en proceso
- **WHEN** el usuario exporta un conteo `EN_PROCESO` con líneas sin contar
- **THEN** esas líneas muestran el stock actual del local como stock sistema y "No contado", y las fechas se muestran en hora de Chile

#### Scenario: Descarga de conteo finalizado
- **WHEN** el usuario exporta un conteo `FINALIZADO`
- **THEN** recibe un archivo `.xlsx` con una fila por línea del conteo y los totales de diferencias

### Requirement: Aislamiento por tenant
Todas las operaciones de conteo MUST operar solo sobre conteos, locales y productos del tenant del usuario autenticado.

#### Scenario: Conteo de otro tenant
- **WHEN** el usuario consulta, modifica o exporta un conteo de otro tenant
- **THEN** el sistema responde 404
