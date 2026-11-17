## MODIFIED Requirements

### Requirement: Recibir compra e impactar inventario

El sistema SHALL permitir transicionar una compra de `PENDIENTE` a **RECIBIDA**
mediante `POST /api/compras/{compra_id}/recibir`. Al recibir, por cada detalle el
sistema suma la cantidad al inventario del local destino (creando el registro de
inventario si no existe), actualiza el `precio_compra` del producto (último costo) y
recalcula su `costo_promedio` ponderado (ver capability `inventario-valorizacion`).
El costo promedio se calcula **antes** de sumar la cantidad al stock. Una compra
recibida es inmutable.

#### Scenario: Recibir compra

- **WHEN** un usuario hace `POST /api/compras/{compra_id}/recibir` sobre una compra `PENDIENTE`
- **THEN** el sistema marca la compra como `RECIBIDA`, suma las cantidades al inventario
  del `local_id`, actualiza el `precio_compra` de cada producto y recalcula su `costo_promedio`

#### Scenario: Factor de conversión de compra

- **WHEN** un producto tiene `factor_conversion_compra` (ej. se compra en sacos de 25 kg)
- **THEN** la cantidad ingresada al inventario es `cantidad × factor_conversion_compra`,
  el `precio_compra` registrado es el `precio_unitario` (precio por **unidad de compra**, ej. el saco,
  que es como lo usan el formulario de productos y el costeo de recetas) y el costo promedio
  se recalcula con `precio_unitario / factor_conversion_compra` (precio por unidad de inventario)

#### Scenario: Inventario inexistente

- **WHEN** no existe registro de inventario para el `producto_id` y `local_id` de la compra
- **THEN** el sistema crea el registro con stock inicial 0 antes de sumar la cantidad recibida

#### Scenario: Compra ya recibida

- **WHEN** se intenta recibir una compra que ya está `RECIBIDA`
- **THEN** el sistema responde `400` "La compra ya fue recibida" y no vuelve a impactar el inventario ni el costo promedio
