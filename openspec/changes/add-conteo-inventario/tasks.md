# Tasks

## 1. Modelo de datos y migración

- [x] 1.1 Agregar modelos `ConteoInventario` y `ConteoInventarioItem` en `database/models.py` y columna nullable `usuario_id` (FK users) en `MovimientoInventario`; verificar que la app importa sin errores
- [x] 1.2 Crear migración Alembic (tablas, unique `conteo_id+producto_id`, índice único parcial `local_id WHERE estado='EN_PROCESO'`, columna `usuario_id`) con `downgrade`; verificar `alembic upgrade head` y `alembic downgrade -1` en BD local
- [x] 1.3 Agregar `openpyxl` a `requirements.txt`; verificar `pip install -r requirements.txt` e `import openpyxl`

## 2. Servicio y API de conteo (captura)

- [x] 2.1 Crear schemas en `schemas/conteo_inventario.py` (create, item update, list/detail responses, filtros); verificar que validan `cantidad_contada >= 0` (400 en negativo)
- [x] 2.2 Implementar en `services/conteo_inventario_service.py` iniciar conteo (COMPLETO precarga productos activos con inventario en el local; PARCIAL vacío; 409 si hay uno EN_PROCESO; 404 local de otro tenant) con tests en `tests/`
- [x] 2.3 Implementar agregar productos (por ids o `categoria_id`, sin duplicados) y quitar línea (solo PARCIAL y EN_PROCESO) con tests
- [x] 2.4 Implementar registrar cantidad contada (guarda stock_sistema actual, diferencia, usuario y fecha; recaptura al corregir; 409 si el conteo está cerrado) con tests
- [x] 2.5 Crear `routers/conteos_inventario.py` con endpoints `def` síncronos (POST /, GET /, GET /{id}, POST/DELETE/PUT items) usando `get_current_active_user`, registrarlo en `main.py`; verificar en `/docs` y con requests contra el backend local

## 3. Finalización, cancelación y auditoría

- [x] 3.1 Implementar finalizar en una transacción con `FOR UPDATE` (ajuste = diferencia sobre stock actual, truncado a 0, crea fila de inventario si falta, movimiento `AJUSTE_CONTEO` con `referencia_id`, `usuario_id` y texto `usuario`; 400 si no hay líneas contadas) con tests de: ajuste simple, ventas posteriores a la captura (12→10, venta 3 ⇒ 7), líneas sin diferencia/no contadas, rollback ante error
- [x] 3.2 Implementar cancelar (sin tocar stock) e inmutabilidad de conteos cerrados (409 en cualquier modificación o doble finalización) con tests
- [x] 3.3 Implementar listado con filtros (local, estado, fechas, usuario) y conteos de líneas contadas/con diferencia; tests de aislamiento por tenant (404 en conteo ajeno)

## 4. Exportación Excel

- [x] 4.1 Implementar `GET /conteos-inventario/{id}/excel` con openpyxl (encabezado + filas SKU, producto, categoría, unidad, sistema, contado, diferencia, usuario, fecha + totales) como `StreamingResponse`; verificar abriendo el archivo descargado y con test que valida filas

## 5. Backoffice (fme-backoffice)

- [x] 5.1 Agregar cliente API de conteos en `fme-backoffice` y pestaña **Conteo** en `app/admin/inventario/page.tsx` con listado de conteos (filtros, estado, antigüedad de abiertos) y modal "Nuevo conteo" (local, tipo); verificar en navegador
- [x] 5.2 Crear pantalla de captura: buscador, filtro por categoría, agregar productos (parcial), input numérico por línea con guardado al salir del campo, progreso contadas/total y resaltado de diferencias; verificar en navegador de escritorio y celular/tablet
- [x] 5.3 Agregar acciones Finalizar (resumen de diferencias + confirmación), Cancelar y Exportar Excel en el detalle; verificar que el stock en Existencias cambia tras finalizar
- [x] 5.4 Mostrar movimientos `AJUSTE_CONTEO` en `HistorialTab` con link al conteo; verificar en navegador

## 6. Verificación integral

- [x] 6.1 Recorrer el flujo completo en local (conteo completo y parcial, finalizar, exportar, historial) con un tenant de prueba y verificar stock y movimientos en BD
- [x] 6.2 Ejecutar `openspec validate add-conteo-inventario --strict` y verificar que pasa

## Workflow follow-up

- Deploy (push a main → migración automática vía entrypoint) y asignar el menú/pestaña a los roles correspondientes.
- Validar con el cliente en producción y luego archivar el change (`/opsx:archive`).
