## Why

En la reunión con Masas Estación (2026-11-16) el conteo de inventario quedó como **prioridad 1**. Hoy el stock por local solo se corrige editando a mano la cantidad (`PUT /inventario/producto/{id}/local/{id}`), sin registro de quién lo hizo, cuánto había antes ni la diferencia encontrada. El cliente necesita contar físicamente por local y producto, que el sistema **ajuste el stock automáticamente** y que quede **auditoría de quién hizo el conteo**.

## What Changes

- Nuevo concepto **Conteo de inventario**: un documento por local con estado `EN_PROCESO` → `FINALIZADO` (o `CANCELADO`), creado por un usuario.
  - **Conteo completo**: se precargan todos los productos activos con inventario en el local.
  - **Conteo parcial**: el usuario agrega solo los productos que quiere contar (por búsqueda o filtro por categoría).
- Por cada línea se registra: producto, stock del sistema al momento de contar, cantidad contada, diferencia, usuario y fecha de la captura.
- Al **finalizar** el conteo, el sistema ajusta automáticamente `inventario.cantidad_stock` de cada línea con diferencia ≠ 0 y genera un `MovimientoInventario` tipo `AJUSTE_CONTEO` que referencia el conteo y el usuario.
- Un conteo finalizado es **inmutable** (registro de auditoría). Se puede consultar el historial de conteos por local, fecha y usuario.
- **Exportar a Excel** el detalle de un conteo (sistema vs contado vs diferencia).
- Nueva pestaña **"Conteo"** en `/admin/inventario` del backoffice.
- `MovimientoInventario` gana una referencia opcional al usuario (`usuario_id`) además del texto `usuario` existente (no rompe compatibilidad).

Fuera de alcance: productos con trazabilidad por lote/caja variable (se gestionan en Stock Cajas), valorización del conteo, y conteo offline.

## Capabilities

### New Capabilities
- `inventario-conteo`: Conteo físico de inventario por local (completo o parcial), con captura por producto, ajuste automático de stock al finalizar, auditoría inmutable (usuario, fecha, sistema vs contado) y exportación a Excel.

### Modified Capabilities
<!-- Ninguna: no existe spec previa de inventario en openspec/specs/. -->

## Impact

- **Modelos / migración (Alembic)**: nuevas tablas `conteos_inventario` y `conteo_inventario_items`; columna nullable `usuario_id` en `movimientos_inventario`.
- **Backend**: nuevo router `routers/conteos_inventario.py` (+ schemas y service); registro en `main.py`.
- **Dependencia**: `openpyxl` en `requirements.txt` (no existe hoy exportación Excel en el backend).
- **Backoffice**: `fme-backoffice/app/admin/inventario/` — nueva pestaña `ConteoTab.tsx` junto a Existencias / Transferencias / Historial; el Historial mostrará movimientos `AJUSTE_CONTEO`.
- **Multi-tenant**: todo filtrado por `tenant_id` del usuario (local y productos del tenant).
