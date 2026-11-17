## Context

`ExistenciasTab.tsx` arma la matriz en el navegador con `GET /api/productos/?limit=1000` (todos, incluidos inactivos), `GET /api/locales/` y `GET /api/inventario/?limit=10000`, y calcula el semáforo en el cliente. `tipos_producto.afecta_inventario` (false para Insumo, Servicio, Operacional) ya existe y lo usa producción para no descontar stock.

## Goals / Non-Goals

**Goals:** vista correcta y completa, filtros por categoría y local, Excel con la misma regla.

**Non-Goals:** valorización en pesos (change aparte del backlog del cliente); edición de stock mínimo/crítico desde aquí.

## Decisions

- **`GET /inventario/existencias`** (filtros opcionales `local_id`, `categoria_id`, `q`, `solo_alertas`) devuelve productos activos con `tipo.afecta_inventario = true`, cada uno con stock por local activo (WEB = suma de los demás) y estado del semáforo. Una sola query con join (productos × locales × left join inventario), sin tope.
  - *Alternativa*: seguir armando en el cliente — duplica la regla del semáforo en el Excel.
- **`GET /inventario/existencias/excel`** reutiliza la misma función; fila por producto y local; columna de estado con color.
- **Orden de locales**: alfabético, WEB al final (consolidado).
- Filtros de texto se aplican en el cliente sobre el resultado (respuesta inmediata); categoría/local/alertas se envían al backend para que el Excel coincida.
- Endpoints `def` síncronos.

## Risks / Trade-offs

- [Respuesta grande con muchos productos × locales] → payload compacto (ids y números); volumen actual ~200 productos × 5 locales.
- [Productos con `afecta_inventario=false` que el cliente sí quiere ver] → se muestran en Productos; confirmar con el cliente al probar.

## Migration Plan

Sin migraciones. Deploy backend y luego backoffice.
