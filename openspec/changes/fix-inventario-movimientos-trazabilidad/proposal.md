## Why

El Historial debe responder "quién movió este stock", pero la transferencia directa registra siempre `usuario="admin"` y ningún movimiento llena la FK `usuario_id`. Además merma y transferencia solo aceptan cantidades enteras aunque el stock se guarda con 3 decimales, lo que impide operar productos por kilo o litro. Y transferencia directa y solicitudes mueven stock con dos implementaciones distintas y sin bloqueo de concurrencia. Ver brechas en `document-inventario-baseline/design.md`.

## What Changes

- **Servicio común de movimientos** (`services/inventario_movimientos.py`): una sola función para transferir stock entre locales y otra para merma, con validaciones, bloqueo de fila (`FOR UPDATE`) y registro del movimiento con usuario real (`usuario` nombre + `usuario_id`).
- **Transferencia directa** y **merma** usan ese servicio: registran el usuario autenticado y aceptan cantidades mayores a 0 con hasta 3 decimales.
- Backoffice: inputs de cantidad con decimales en Transferencias y Merma.
- No se toca el flujo de Solicitudes aquí (lo migra `improve-solicitudes-transferencia` al mismo servicio).

## Capabilities

### New Capabilities
<!-- Ninguna -->

### Modified Capabilities
- `inventario-transferencias`: "Transferencia directa entre locales" acepta decimales, registra el usuario y se protege contra concurrencia.
- `inventario-existencias`: "Registro de merma" acepta decimales.
- `inventario-historial`: agrega "Usuario responsable en cada movimiento".

## Impact

- Backend: nuevo `services/inventario_movimientos.py`; `routers/movimientos_inventario.py`, `routers/inventario.py` (ajuste-merma), `schemas/movimiento_inventario.py` (`cantidad` decimal).
- Backoffice: `TransferenciasTab.tsx`, `ExistenciasTab.tsx` (inputs `step="0.001"`, sin `parseInt`).
- Usa la columna `movimientos_inventario.usuario_id` creada por `add-conteo-inventario`. Archivar después de `add-conteo-inventario` y `document-inventario-baseline`.
