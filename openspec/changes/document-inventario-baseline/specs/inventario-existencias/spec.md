# Spec Delta

## Purpose

Permite consultar el stock de cada producto en cada local del tenant, identificar rápidamente productos bajo stock mínimo o crítico y registrar mermas que descuentan stock de un local con trazabilidad del usuario.

## ADDED Requirements

### Requirement: Módulo Inventario con pestañas
El backoffice SHALL ofrecer en `/admin/inventario` las pestañas **Existencias**, **Conteo**, **Transferencias** e **Historial**, con Existencias como pestaña inicial, y un acceso a **Stock de Cajas**. La pestaña Conteo se rige por la capability `inventario-conteo`.

#### Scenario: Ingreso al módulo
- **WHEN** el usuario entra a `/admin/inventario`
- **THEN** ve las cuatro pestañas y la pestaña Existencias seleccionada

### Requirement: Stock por producto y local
Existencias SHALL mostrar, por cada producto del tenant ordenado alfabéticamente, su SKU, stock mínimo, stock crítico y la cantidad en stock en cada local activo. Un local sin registro de inventario para el producto MUST mostrarse con stock 0.

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

### Requirement: Local WEB consolidado
Para el local con código `WEB` (tienda online), Existencias SHALL mostrar como stock la suma del stock del producto en todos los demás locales, identificado como "(WEB / Global)", y MUST NOT permitir registrar merma sobre él.

#### Scenario: Stock global en WEB
- **GIVEN** un producto con 10 en Lampa y 5 en TilTil
- **WHEN** el usuario ve el producto en Existencias
- **THEN** el local WEB muestra 15 y no tiene botón de merma

### Requirement: Semáforo de alertas de stock
Cada par producto/local SHALL mostrar un indicador: rojo si el stock mostrado es ≤ stock crítico del producto, amarillo si es ≤ stock mínimo, y verde en otro caso. Un stock mínimo o crítico no definido se considera 0.

#### Scenario: Stock bajo el mínimo
- **GIVEN** un producto con stock mínimo 20, crítico 5 y stock 12 en Lampa
- **WHEN** el usuario ve Existencias
- **THEN** Lampa se muestra en amarillo

#### Scenario: Stock en nivel crítico
- **GIVEN** un producto con stock crítico 5 y stock 3 en Lampa
- **WHEN** el usuario ve Existencias
- **THEN** Lampa se muestra en rojo

### Requirement: Búsqueda y filtro de alertas
Existencias SHALL permitir filtrar productos por texto contenido en el nombre o SKU (sin distinguir mayúsculas) y, con la opción "Solo mostrar alertas", mostrar solo productos que tengan al menos un local en amarillo o rojo.

#### Scenario: Solo alertas
- **WHEN** el usuario activa "Solo mostrar alertas"
- **THEN** se ocultan los productos cuyos locales están todos en verde

### Requirement: Registro de merma
Existencias SHALL permitir registrar una merma (pérdida, daño, vencimiento) para un producto en un local físico, indicando una cantidad entera mayor a 0 y un motivo opcional. La merma MUST descontar la cantidad del stock del local, MUST NOT dejar stock negativo y MUST registrar un movimiento tipo `MERMA` con el usuario que la realizó.

#### Scenario: Merma válida
- **GIVEN** stock 10 del producto en Lampa
- **WHEN** el usuario registra una merma de 3 con motivo "Producto vencido"
- **THEN** el stock queda en 7 y existe un movimiento `MERMA` de 3 con el motivo y el nombre del usuario

#### Scenario: Merma mayor al stock
- **WHEN** el usuario registra una merma mayor al stock disponible
- **THEN** el sistema la rechaza con un error y el stock no cambia

#### Scenario: Cantidad no positiva
- **WHEN** el usuario registra una merma de 0 o negativa
- **THEN** el sistema la rechaza con un error y el stock no cambia

#### Scenario: Local sin stock
- **WHEN** el stock del producto en el local es 0
- **THEN** la acción de merma está deshabilitada

### Requirement: Aislamiento por tenant en existencias
La consulta de inventario y el registro de merma MUST operar solo sobre productos y locales del tenant del usuario autenticado.

#### Scenario: Merma sobre producto de otro tenant
- **WHEN** el usuario intenta registrar merma de un producto o local que no pertenece a su tenant
- **THEN** el sistema responde 404 y no modifica stock
