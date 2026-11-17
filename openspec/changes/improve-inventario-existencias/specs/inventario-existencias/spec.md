## MODIFIED Requirements

### Requirement: Stock por producto y local
Existencias SHALL mostrar, por cada producto activo del tenant cuyo tipo maneja stock (tipo de producto que afecta inventario), ordenado alfabéticamente, su SKU, categoría, unidad, stock mínimo, stock crítico y la cantidad en stock en cada local activo, sin límite de cantidad de productos. Los locales se muestran en orden alfabético con el local WEB al final. Un local sin registro de inventario para el producto MUST mostrarse con stock 0.

#### Scenario: Producto sin inventario en un local
- **GIVEN** un producto sin registro de inventario en el local "TilTil"
- **WHEN** el usuario abre Existencias
- **THEN** el producto muestra stock 0 en "TilTil"

#### Scenario: Local inactivo
- **WHEN** un local está marcado como inactivo
- **THEN** no aparece en la lista de stock de ningún producto

#### Scenario: Sin datos base
- **WHEN** el tenant no tiene productos o no tiene locales
- **THEN** se muestra el mensaje "Necesitas crear productos y locales primero."

#### Scenario: Producto operacional o inactivo
- **GIVEN** un producto "ARRIENDO" de tipo Operacional y un producto inactivo
- **WHEN** el usuario abre Existencias
- **THEN** ninguno de los dos aparece

#### Scenario: Catálogo grande
- **GIVEN** el tenant tiene 1500 productos activos que manejan stock
- **WHEN** el usuario abre Existencias
- **THEN** los 1500 productos están disponibles en la vista

### Requirement: Búsqueda y filtro de alertas
Existencias SHALL permitir filtrar productos por texto contenido en el nombre o SKU (sin distinguir mayúsculas), por categoría y por local, y, con la opción "Solo mostrar alertas", mostrar solo productos que tengan al menos un local visible en amarillo o rojo. Los filtros son combinables.

#### Scenario: Solo alertas
- **WHEN** el usuario activa "Solo mostrar alertas"
- **THEN** se ocultan los productos cuyos locales visibles están todos en verde

#### Scenario: Filtro por categoría y local
- **WHEN** el usuario filtra por categoría "Abarrotes" y local "Lampa"
- **THEN** solo se muestran productos de Abarrotes con su stock en Lampa

## ADDED Requirements

### Requirement: Exportar existencias a Excel
Existencias SHALL poder descargarse como archivo `.xlsx` con los filtros aplicados, con una fila por producto y local que incluya SKU, producto, categoría, unidad, local, stock, stock mínimo, stock crítico y estado (OK / Mínimo / Crítico).

#### Scenario: Exportar inventario bajo de una tienda
- **GIVEN** el usuario filtró por local "TilTil" y activó "Solo mostrar alertas"
- **WHEN** presiona "Exportar Excel"
- **THEN** descarga un `.xlsx` solo con los productos en Mínimo o Crítico en TilTil

#### Scenario: Aislamiento por tenant en la exportación
- **WHEN** el usuario exporta existencias
- **THEN** el archivo contiene solo productos y locales de su tenant
