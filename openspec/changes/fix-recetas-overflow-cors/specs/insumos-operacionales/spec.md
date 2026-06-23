## ADDED Requirements

### Requirement: Clasificación de productos por afectación de inventario

El sistema SHALL distinguir los productos que afectan inventario (insumos físicos)
de los operacionales (costos sin stock, como arriendo, electricidad, HH de producción o
desgaste de maquinaria) mediante el atributo `afecta_inventario` del tipo de producto
(`TipoProducto`). Por defecto un tipo de producto SHALL afectar inventario.

#### Scenario: Tipo operacional no afecta inventario

- **WHEN** un producto pertenece a un tipo con `afecta_inventario = false`
  (por ejemplo el tipo `SERVICIO`)
- **THEN** el sistema lo considera un costo operacional que no maneja stock

#### Scenario: El flag se administra desde el mantenedor de tipos

- **WHEN** un administrador edita un tipo de producto en el mantenedor de Tipos de Producto
- **THEN** puede marcar/desmarcar `afecta_inventario` y el cambio aplica a todos los
  productos de ese tipo, sin cambios de código

#### Scenario: Visibilidad del tipo en el formulario de receta

- **WHEN** un usuario arma o consulta los ingredientes de una receta en el backoffice
- **THEN** cada ingrediente muestra su tipo de producto y si afecta inventario
  (etiqueta "Operacional · sin stock" vs "Afecta inventario")

#### Scenario: Tipo físico afecta inventario por defecto

- **WHEN** un producto pertenece a un tipo sin `afecta_inventario` definido explícitamente
- **THEN** el sistema lo trata como insumo físico que afecta inventario

### Requirement: Producción ignora stock de insumos operacionales

El sistema SHALL omitir, al validar disponibilidad y al descontar stock para una orden
de producción, los ingredientes de la receta cuyo producto no afecta inventario, pero
SHALL seguir incluyendo su costo en el costeo de la receta.

#### Scenario: Orden con insumos mixtos

- **WHEN** una receta incluye insumos físicos (harina, manteca) e insumos operacionales
  (arriendo, electricidad) y se valida/ejecuta una orden de producción
- **THEN** el sistema valida y descuenta stock solo de los insumos físicos, y no exige
  ni descuenta stock de los operacionales

#### Scenario: Costo operacional sí se contabiliza

- **WHEN** se calcula el costo de una receta que incluye insumos operacionales
- **THEN** el costo de los insumos operacionales se suma al costo total de la receta
  igual que el de los insumos físicos
