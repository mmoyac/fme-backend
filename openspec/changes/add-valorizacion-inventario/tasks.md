## 1. Modelo y migración

- [x] 1.1 Agregar `costo_promedio = Column(Numeric(12, 4), nullable=True)` a `Producto` en `database/models.py`
- [x] 1.2 Migración Alembic: agregar la columna y hacer el backfill `COALESCE(precio_compra, costo_fabricacion)`, con downgrade
- [x] 1.3 Exponer `costo_promedio` en las respuestas de productos (`routers/productos.py`)

## 2. Servicio de costo promedio

- [x] 2.1 Crear `services/costo_promedio.py` con `registrar_entrada_costo(db, producto, cantidad, costo_unitario)` (stock total del tenant, `FOR UPDATE`, reset si stock ≤ 0 o costo nulo)
- [x] 2.2 Llamarlo desde `routers/compras.py` al recibir, antes de sumar el stock, con la cantidad y el costo convertidos por `factor_conversion_compra`
- [x] 2.3 Llamarlo desde `routers/produccion.py` al finalizar, con la cantidad real y `costo_fabricacion`, solo si este no es nulo

## 3. Reporte de valorización

- [x] 3.1 Schemas `ValorizacionItem` y `ValorizacionResponse` (filas + totales + margen global)
- [x] 3.2 Función `calcular_valorizacion(db, tenant_id, local_id, categoria_id, q)` con el join a precios, el cálculo neto de IVA y los flags `sin_costo`, `sin_precio` y `stock_negativo`
- [x] 3.3 `GET /api/inventario/valorizacion` (sincrónico, tenant + `local_de_alcance`)
- [x] 3.4 Agregar `openpyxl` a `requirements.txt` y `GET /api/inventario/valorizacion/excel` (encabezados en español, fila de totales, nombre con fecha)

## 4. Backoffice

- [x] 4.1 `lib/api/valorizacion.ts`: obtener el reporte y descargar el Excel (blob con token)
- [x] 4.2 `app/admin/inventario/components/ValorizacionTab.tsx`: tarjetas de totales, filtros (local con alcance, categoría, búsqueda), tabla e insignias
- [x] 4.3 Agregar la pestaña "Valorización" en `app/admin/inventario/page.tsx`

## 5. Verificación

- [ ] 5.1 Probar en el contenedor fme-backend: migración, recepción de una compra (incluido el caso con factor) y finalización de una producción, verificando el promedio
- [ ] 5.2 Probar el reporte y el Excel como admin y como usuario de tienda; cuadrar los totales a mano con 2 o 3 productos

## Actualizar capacitación

- [ ] Revisar `capacitacion/inventario/07-valorizacion.html` contra la pantalla final (ya creada en add-centro-capacitacion) y actualizar su fecha de "Última revisión" si cambia

