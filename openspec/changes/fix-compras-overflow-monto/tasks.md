## 1. Modelo de datos

- [x] 1.1 Cambiar `Compra.monto_total` de `Numeric(10, 2)` a `Numeric(12, 2)` en `database/models.py`
- [x] 1.2 Cambiar `DetalleCompra.precio_unitario` de `Numeric(10, 2)` a `Numeric(12, 2)` en `database/models.py`
- [x] 1.3 Cambiar `Producto.precio_compra` de `Numeric(10, 2)` a `Numeric(12, 2)` en `database/models.py`

## 2. Migración Alembic

- [x] 2.1 Generar nueva revisión Alembic en `migrations/versions/`
- [x] 2.2 Implementar `upgrade()` con `op.alter_column` a `Numeric(12, 2)` para las 3 columnas
- [x] 2.3 Implementar `downgrade()` que revierta a `Numeric(10, 2)` las 3 columnas
- [x] 2.4 Verificar que `alembic upgrade head` corre sin errores en desarrollo

## 3. Manejo de errores en el router

- [x] 3.1 Envolver el `db.commit()` de `create_compra` en `try/except IntegrityError, DataError` con `rollback` y `HTTPException(400, ...)` legible
- [x] 3.2 Aplicar el mismo manejo de errores a `update_compra`
- [x] 3.3 Aplicar el mismo manejo de errores a `recibir_compra`

## 4. Verificación en desarrollo

- [x] 4.1 Crear una compra con `monto_total > 100.000.000` y confirmar que persiste (no 500)
- [x] 4.2 Recibir esa compra y confirmar que el inventario y `precio_compra` se actualizan sin error
- [x] 4.3 Provocar un error de persistencia (p. ej. FK inválida) y confirmar respuesta `400` con mensaje legible
- [x] 4.4 Validar la change con `openspec validate fix-compras-overflow-monto`

## 5. Despliegue a producción

- [ ] 5.1 Confirmar con el usuario que dev quedó validado
- [ ] 5.2 Push a `main` (GitHub Actions → VPS; migración corre automáticamente vía entrypoint)
- [ ] 5.3 Verificar en producción que la creación de la compra original funciona
