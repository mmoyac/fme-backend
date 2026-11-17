# Design

## Context

- Loyverse (que el cliente usa hoy) valoriza el inventario con el **costo promedio** del artículo, que es global para todas las tiendas. Su reporte muestra stock, costo, valor de inventario, valor de venta, ganancia potencial y margen, con filtros por tienda y categoría, y se puede exportar.
- EffiChain tiene hoy: `Producto.precio_compra` (último costo neto, sobrescrito en `routers/compras.py` al recibir una compra), `Producto.costo_fabricacion` (calculado desde la receta), `Inventario.cantidad_stock` por local y `Precio.monto_precio` por producto, local y unidad de medida.
- Los costos de compra se ingresan **netos** (confirmado por el usuario el 17-11-26).
- El alcance por local se resuelve con `utils/alcance_local.py` (`local_de_alcance`, `exigir_local`).

## Goals / Non-Goals

**Goals:** costo promedio ponderado que siga a compras y producción; reporte de valorización en vivo por producto y local; exportación a Excel; pestaña en el backoffice.

**Non-Goals:** valorización a una fecha pasada (requiere snapshots, queda como mejora futura); costo por local; FIFO/PEPS; recalcular el promedio histórico desde compras antiguas; valorizar `stock_cajas_proveedor`.

## Decisions

1. **Promedio global por producto, columna en `productos`.** Es igual que Loyverse y no requiere una tabla nueva. Se descartó el costo por local porque las transferencias tendrían que mover costo y eso complica todo sin que el cliente lo haya pedido.
2. **Servicio único `services/costo_promedio.py`** con `registrar_entrada_costo(db, producto, cantidad, costo_unitario)`. Calcula el stock total del tenant con `SUM(inventario.cantidad_stock)` y bloquea la fila del producto con `with_for_update()` para que dos entradas simultáneas no se pisen. Se llama **antes** de sumar al stock, tanto desde compras como desde producción. Queda alineado con el servicio común que propone `fix-inventario-movimientos-trazabilidad`.
3. **Precisión `NUMERIC(12,4)`.** Así el promedio no acumula error de redondeo con costos por gramo o por kg. En pantalla se muestra en pesos enteros.
4. **El precio de venta se toma de `Precio`** del local, en la unidad de medida del producto. Si `precio_incluye_iva` es true, se divide por 1,19, de modo que costo y venta se comparan en neto.
5. **El reporte se calcula en SQL**, con un join `inventario` → `productos` → `categorias` → `locales` y un left join a `precios`, filtrando `cantidad_stock != 0` y por tenant. Las sumas se hacen en Python sobre las filas, porque el volumen es bajo (cientos de filas).
6. **Excel en el backend con `openpyxl`.** Reutiliza la misma función del reporte, así que lo que se ve y lo que se exporta coinciden siempre. El backoffice hoy no tiene librería xlsx. El mismo helper sirve después para los demás "exportar a Excel" que pidió el cliente (historial, productos, compras, precios).
7. **Endpoints sincrónicos (`def`, no `async def`)**, por el incidente del event loop del 11-11.

## Risks / Trade-offs

- **El costo inicial no es un promedio real.** El backfill usa el último costo, así que el promedio solo se vuelve "real" con las compras siguientes. Se informa al cliente.
- **Stock negativo.** Si el stock total es ≤ 0, el promedio se resetea al costo entrante. Es el comportamiento de Loyverse y evita divisiones absurdas.
- **Productos de reventa sin compras registradas** quedan "Sin costo". Es intencional: se ven en el reporte para completarlos.
- **Una compra con un precio mal ingresado** contamina el promedio y no se revierte al eliminar la compra, porque una compra recibida ya es inmutable. Se acepta por ahora.

## Migration Plan

Migración Alembic: `ADD COLUMN costo_promedio NUMERIC(12,4) NULL` y luego `UPDATE productos SET costo_promedio = COALESCE(precio_compra, costo_fabricacion)`. El downgrade elimina la columna. Corre automáticamente en el entrypoint al hacer deploy.
