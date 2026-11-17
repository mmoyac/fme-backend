## ADDED Requirements

### Requirement: Costo promedio ponderado por producto

El sistema SHALL mantener en cada producto un `costo_promedio` neto, expresado por unidad de inventario y global para el tenant (no por local). Cuando entran unidades con un costo conocido, el sistema SHALL recalcularlo así:
`nuevo = (stock_total × costo_promedio + cantidad_entrante × costo_entrante) / (stock_total + cantidad_entrante)`.
`stock_total` es la suma de `cantidad_stock` del producto en todos los locales del tenant, **antes** de sumar la entrada.

#### Scenario: Entrada por compra recibida
- **WHEN** se recibe una compra de un producto con stock total 10, costo promedio 1.000 y entran 10 unidades a 1.200 neto por unidad de inventario
- **THEN** el `costo_promedio` del producto queda en 1.100

#### Scenario: Sin stock previo o costo previo nulo
- **WHEN** el stock total previo es ≤ 0 o el `costo_promedio` es nulo
- **THEN** el `costo_promedio` queda igual al costo entrante

#### Scenario: Factor de conversión
- **WHEN** el producto se compra en sacos (`factor_conversion_compra` = 25) a 25.000 el saco
- **THEN** el costo entrante es 1.000 por unidad de inventario y la cantidad entrante es `cantidad × 25`

#### Scenario: Entrada por producción
- **WHEN** se finaliza una orden de producción y entra el producto terminado
- **THEN** el `costo_promedio` del producto se recalcula usando la cantidad real producida y su `costo_fabricacion` como costo entrante; si `costo_fabricacion` es nulo, el costo promedio no cambia

#### Scenario: Movimientos sin costo
- **WHEN** hay una transferencia, un ajuste, una merma, un conteo o una venta
- **THEN** el `costo_promedio` no cambia

#### Scenario: Inicialización
- **WHEN** se aplica la migración
- **THEN** cada producto queda con `costo_promedio` = `precio_compra`, si no hay, `costo_fabricacion`, y si tampoco hay, nulo

### Requirement: Reporte de valorización de inventario

El sistema SHALL exponer `GET /api/inventario/valorizacion` (autenticado y aislado por tenant), que devuelve una fila valorizada por producto y local con stock distinto de cero, los totales y el margen global, y SHALL aceptar los filtros opcionales `local_id`, `categoria_id` y `q` (busca por nombre o SKU).

#### Scenario: Cálculo de una fila
- **WHEN** se valoriza una fila de inventario
- **THEN** incluye `stock`, `costo_unitario` (costo promedio neto), `valor_inventario` = stock × costo_unitario, `precio_venta_neto` (precio del local en la unidad del producto, dividido por 1,19 si `precio_incluye_iva`), `valor_venta` = stock × precio_venta_neto, `ganancia_potencial` = valor_venta − valor_inventario y `margen_pct` = ganancia_potencial / valor_venta × 100

#### Scenario: Valorización de todos los locales
- **WHEN** un administrador consulta sin `local_id`
- **THEN** recibe las filas de todos los locales del tenant y los totales consolidados

#### Scenario: Usuario de tienda
- **WHEN** un usuario con local asignado (no admin) consulta
- **THEN** solo recibe filas de su local, aunque envíe otro `local_id`

#### Scenario: Producto sin costo
- **WHEN** un producto tiene `costo_promedio` nulo
- **THEN** la fila se incluye con `costo_unitario`, `valor_inventario`, `ganancia_potencial` y `margen_pct` nulos, con `sin_costo = true`, y no suma a los totales de costo ni de ganancia

#### Scenario: Producto sin precio de venta
- **WHEN** no existe precio para el producto en ese local
- **THEN** la fila se incluye con `precio_venta_neto`, `valor_venta`, `ganancia_potencial` y `margen_pct` nulos, con `sin_precio = true`

#### Scenario: Stock negativo
- **WHEN** el stock de una fila es negativo
- **THEN** la fila se incluye con sus valores calculados (negativos), con `stock_negativo = true`, para que se pueda corregir

### Requirement: Exportar valorización a Excel

El sistema SHALL exponer `GET /api/inventario/valorizacion/excel`, con los mismos filtros y el mismo alcance que el reporte, y responder un archivo `.xlsx` con una fila por registro, una fila de totales al final, encabezados en español y el nombre `valorizacion_inventario_<AAAA-MM-DD>.xlsx`.

#### Scenario: Exportar con filtros
- **WHEN** el usuario exporta filtrando por un local y una categoría
- **THEN** el Excel contiene exactamente las filas y los totales que muestra el reporte con esos filtros

### Requirement: Pestaña Valorización en Inventario

El backoffice SHALL mostrar en Inventario una pestaña **Valorización** con:
- tarjetas de totales (valor inventario, valor venta, ganancia potencial y margen);
- una tabla con producto, SKU, categoría, local, stock, costo, valor inventario, precio venta, valor venta, ganancia y margen;
- filtros de local (solo para quien tiene alcance total), categoría y búsqueda;
- un botón **Exportar a Excel**;
- insignias "Sin costo", "Sin precio" y "Stock negativo".

#### Scenario: Valores netos explicados
- **WHEN** el usuario abre la pestaña o el Excel
- **THEN** todos los montos se muestran netos (sin IVA), un aviso explica que el costo es promedio ponderado neto y que el precio de venta neto es el precio con IVA ÷ 1,19, y cada precio neto muestra como referencia el precio con IVA del local

#### Scenario: Usuario de tienda en la pestaña
- **WHEN** un usuario de tienda abre la pestaña
- **THEN** el selector de local está fijo en su local
