## MODIFIED Requirements

### Requirement: Listar y consultar compras

El sistema SHALL permitir listar las compras del tenant y consultar una compra por id,
incluyendo sus detalles. La consulta del detalle SHALL estar disponible para una
compra en **cualquier estado** (PENDIENTE o RECIBIDA), y el cliente (backoffice) SHALL
ofrecer una vista de solo lectura para consultarlo sin necesidad de editar la compra.

#### Scenario: Listar compras

- **WHEN** un usuario hace `GET /api/compras/`
- **THEN** el sistema responde las compras del tenant ordenadas por `id` descendente (las nuevas primero)

#### Scenario: Consultar una compra

- **WHEN** un usuario hace `GET /api/compras/{compra_id}` de una compra de su tenant
- **THEN** el sistema responde la compra con su cabecera, `estado`, `monto_total` y `detalles`

#### Scenario: Consultar el detalle de una compra recibida

- **WHEN** un usuario consulta una compra cuyo estado es `RECIBIDA`
- **THEN** el sistema responde su cabecera y `detalles` igual que para una compra
  `PENDIENTE`, sin requerir que la compra sea editable

#### Scenario: Acceso a la vista de detalle desde la lista

- **WHEN** el usuario ve la lista de compras en el backoffice y elige "Ver" sobre una
  compra (incluida una `RECIBIDA`)
- **THEN** se muestra una vista de solo lectura con la cabecera, la tabla de detalle
  (producto, cantidad, precio unitario, subtotal) y el monto total, sin permitir editar
