## 1. Migraciones de base de datos

- [x] 1.1 Migración Alembic: `ingredientes_receta.cantidad` → `Numeric(18,8)`
- [x] 1.2 Migración Alembic: agregar `tipos_producto.afecta_inventario` (bool, default `true`)
- [x] 1.3 Actualizar `database/models.py` (`IngredienteReceta.cantidad`, `TipoProducto.afecta_inventario`)
- [x] 1.4 Exponer `afecta_inventario` en el schema/endpoints del mantenedor de Tipos de Producto (backend) y agregar la casilla en el mantenedor del backoffice

## 2. CORS en respuestas de error

- [x] 2.1 En `main.py`, envolver `await call_next(request)` de `DynamicCORSMiddleware.dispatch` en `try/except`
- [x] 2.2 Ante excepción, loggear el traceback y devolver `JSONResponse(500)` con cabeceras CORS si el origen es permitido
- [ ] 2.3 Verificar que respuestas exitosas, preflight `OPTIONS` y origen no permitido siguen igual

## 3. Precisión de cantidad y validación

- [x] 3.1 En `schemas/receta.py`, soportar `cantidad` con 8 decimales (sin truncar a 3) y validar el rango contra `Numeric(18,8)`
- [x] 3.2 Agregar util para `quantize` a escala 2 (costos) y validar que la parte entera cabe en `Numeric(10,2)`
- [x] 3.3 Devolver `HTTPException(422)` con mensaje legible cuando un valor exceda el límite de columna

## 4. Cálculo de costos acotado

- [x] 4.1 En `calcular_costos_receta`, aplicar `quantize(Decimal("0.01"))` a `costo_unitario_referencia`, `costo_total_calculado`, `costo_total` y `costo_unitario_calculado` antes de asignar
- [x] 4.2 Usar la `cantidad` con su precisión completa (8 decimales) en el cálculo
- [x] 4.3 Quitar el/los `commit()` internos de `calcular_costos_receta` (solo mutar objetos en la sesión)
- [x] 4.4 Manejar división por cero / unidades inválidas con error controlado

## 5. Persistencia atómica

- [x] 5.1 Reestructurar `crear_receta` para construir receta + ingredientes + costos + `producto.tiene_receta`/`costo_fabricacion` y hacer un único `commit()` con `try/except` + `rollback`
- [x] 5.2 Aplicar el mismo patrón (commit único + rollback) en `agregar_ingrediente`, `actualizar_ingrediente`, `eliminar_ingrediente` y `recalcular_costos`
- [x] 5.3 Revisar todos los llamadores de `calcular_costos_receta` para asegurar que el commit lo controla el endpoint

## 6. Producción: insumos operacionales

- [x] 6.1 En `routers/produccion.py`, omitir validación de stock para ingredientes cuyo `producto.tipo_producto.afecta_inventario = false` (helper `_afecta_inventario`)
- [x] 6.2 Omitir también el descuento de stock de esos ingredientes al ejecutar/guardar la orden (loops de `crear_orden` y `finalizar_orden`)
- [x] 6.3 Confirmar que el costeo de la receta sigue incluyendo el costo de los operacionales (sin cambios en `calcular_costos_receta`)
- [x] 6.4 En el formulario de ingredientes de la receta (backoffice), mostrar el tipo de producto y si afecta inventario por ingrediente
- [x] 6.5 Frontend receta: redondear `cantidad` a 8 decimales al agregar (evita artefacto de float + 422), `step` de inputs a 8 decimales, y formatear errores 422 legibles (no "[object Object]")
- [x] 6.6 Impedir ingredientes duplicados: front bloquea agregar un producto ya presente; backend rechaza con 400 en `agregar_ingrediente` y en `crear_receta` (lista con repetidos)

## 7. Verificación

- [x] 7.1 Reproducir el caso original: 8 decimales persisten, overflow se rechaza (HTTPException), recálculo de receta real sin error. Falta cruzar con el Excel del cliente usando su data real.
- [x] 7.2 CORS en error: el middleware adjunta cabeceras también en respuestas 500 (verificado por código; `_a_dinero` lanza HTTPException 422 visible)
- [x] 7.3 Atomicidad: commit único + rollback en todos los endpoints (verificado por código y recálculo real commiteado)
- [ ] 7.4 OT con insumos mixtos: solo se descuenta stock de los físicos; operacionales no exigen stock pero sí costean — pendiente prueba manual en UI con data sembrada
- [ ] 7.5 Tests en `tests/` — BLOQUEADO: el harness de tests está roto por versión de Starlette TestClient (`Client.__init__() got an unexpected keyword argument 'app'`), pre-existente. Requiere arreglar conftest aparte.
- [x] 7.6 `openspec validate fix-recetas-overflow-cors` → válido (la suite de tests está bloqueada por 7.5)
