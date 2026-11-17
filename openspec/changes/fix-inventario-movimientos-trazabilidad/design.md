## Context

Transferencia directa (`routers/movimientos_inventario.py:21-111`) y merma (`routers/inventario.py:205-275`) implementan su propia lógica; solicitudes (`routers/solicitudes_transferencia.py:279-307`) una tercera. Los schemas usan `int` para cantidad mientras `inventario.cantidad_stock` y `movimientos_inventario.cantidad` son `Numeric(10,3)`. `add-conteo-inventario` agregó `movimientos_inventario.usuario_id`.

## Goals / Non-Goals

**Goals:** una implementación única y segura de "mover stock"; usuario real en movimientos; decimales.

**Non-Goals:** migrar Solicitudes al servicio (lo hace `improve-solicitudes-transferencia`); backfill de movimientos históricos con `usuario="admin"`.

## Decisions

- **`services/inventario_movimientos.py`** con `transferir(db, user, producto_id, origen_id, destino_id, cantidad, notas, referencia_id=None, commit=True)` y `registrar_merma(db, user, producto_id, local_id, cantidad, motivo)`. Validan tenant, origen≠destino, existencia y stock; bloquean las filas de `inventario` con `with_for_update()` en orden de `local_id` (evita deadlocks); registran `usuario=nombre_completo or email` y `usuario_id`. `commit=False` permite que Solicitudes agrupe varios ítems en una transacción.
  - *Alternativa*: corregir cada router por separado — mantiene tres implementaciones divergentes.
- **Decimales**: `cantidad` como `condecimal(gt=0, decimal_places=3)` en schemas; el parámetro de merma pasa a `Decimal`. El front usa `step="0.001"` y `parseFloat`.
- **Contrato de respuesta** de `POST /movimientos/transferencia` se mantiene (mensaje, origen, destino, movimiento_id).
- Endpoints `def` síncronos.

## Risks / Trade-offs

- [Clientes que enviaban enteros] → siguen funcionando (un entero es un decimal válido).
- [Movimientos antiguos siguen con "admin"] → aceptado; el historial los muestra como están.

## Migration Plan

Sin migraciones. Deploy backend y luego backoffice.
