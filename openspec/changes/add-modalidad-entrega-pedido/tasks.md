## 1. Modelo y migración

- [x] 1.1 Agregar a `Pedido` las columnas `modalidad_entrega`, `fecha_entrega`, `entregado_por_id` (+ relación), `retirado_por_nombre`, `retirado_por_rut` y `nota_entrega`
- [x] 1.2 Migración Alembic con el backfill (DESPACHO si hay costo_delivery, despacho o ítem de hoja de ruta; si no, RETIRO; fecha_entrega desde la hoja de ruta o el despacho) y downgrade; aplicarla en el contenedor fme-backend

## 2. Backend

- [x] 2.1 `services/entrega_pedido.py` con `registrar_entrega(...)` idempotente
- [x] 2.2 Guardar la modalidad al aceptar una cotización (`modalidad_entrega` o `requiere_delivery`) y al crear un pedido en el backoffice; en el POS directo registrar RETIRO entregado por el vendedor
- [x] 2.3 `POST /api/pedidos/{id}/retiro` (tenant, validación de modalidad y estado, datos opcionales de quién retira)
- [x] 2.4 Hoja de ruta (`/entregar`), despacho (estado ENTREGADO) y `PUT /pedidos/{id}` a ENTREGADO usan `registrar_entrega`
- [x] 2.5 Schemas y respuestas de pedido con los campos de entrega (incluido el nombre de quien entregó); filtros `modalidad_entrega` y `entregado` en el listado
- [x] 2.6 Cobranza: exponer `modalidad_entrega` y `fecha_entrega` en cada cobro

## 3. Backoffice

- [x] 3.1 Aceptar cotización: selector Retiro / Despacho (Despacho = requiere delivery)
- [x] 3.2 Lista de Pedidos: columna de modalidad con estado de entrega y filtros
- [x] 3.3 Detalle de pedido: bloque "Entrega" y botón "Marcar retirado" con modal (nombre, RUT y nota opcionales)
- [x] 3.4 Cobranza: modalidad y fecha de entrega en la tabla

## 4. Verificación

- [ ] 4.1 En local: pedido #00127 (RETIRO) → finalizar OP → CONFIRMADO → marcar retirado → ENTREGADO con quién y cuándo; verlo en Pedidos y Cobranza
- [ ] 4.2 Intentar retirar un pedido DESPACHO o PENDIENTE → 400; entregar uno de despacho desde la hoja de ruta → registra fecha y usuario
