## Why

Hoy el backoffice no permite ver el detalle de una compra **RECIBIDA**: en la lista
solo aparece el texto "Procesada", y la ruta `/admin/compras/{id}` es la pantalla de
edición, que bloquea explícitamente las compras recibidas y redirige a la lista. El
usuario no tiene forma de consultar qué productos, cantidades y precios contiene una
compra ya procesada, pese a que el backend (`GET /api/compras/{id}`) ya expone esos
datos para cualquier estado.

## What Changes

- Agregar una **vista de solo lectura** del detalle de una compra en el backoffice,
  accesible para cualquier estado (PENDIENTE y RECIBIDA), que muestra la cabecera
  (proveedor, local, fecha, tipo y N° de documento, notas, estado) y la tabla de
  detalle (producto, cantidad, precio unitario, subtotal) más el monto total.
- Agregar en la lista de compras un enlace **"Ver"** que abre esa vista; para las
  compras RECIBIDAS reemplaza el texto estático "Procesada".
- No se requieren cambios de backend: `GET /api/compras/{id}` ya devuelve cabecera y
  detalles para cualquier estado.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `compras`: se añade el requisito de poder **consultar el detalle de una compra en
  cualquier estado** (incluida RECIBIDA) desde el cliente.

## Impact

- **Frontend** (`fme-backoffice`): nueva página de detalle de solo lectura y un enlace
  "Ver" en la lista de compras.
- **Backend**: sin cambios (endpoint ya disponible).
- **Compatibilidad**: no breaking; solo agrega lectura.
