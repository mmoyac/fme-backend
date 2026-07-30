## Why

El módulo de Mantenedores (`/admin/mantenedores`) reúne ~20 tablas maestras que hoy se construyeron con "vibe coding", sin una especificación que documente el patrón CRUD común ni el inventario de lo existente. No hay un contrato claro que sirva de base para agregar mantenedores nuevos de forma consistente. Esta spec establece esa línea base para que los próximos mantenedores se propongan y construyan con OpenSpec reusando el patrón ya probado.

## What Changes

- Se documenta como spec base el **patrón CRUD compartido** de los mantenedores: listar (con filtro `activo`), obtener por id, crear, actualizar (parcial), eliminar.
- Se documentan las **reglas transversales** observadas en el código actual:
  - Autorización: lecturas con usuario activo; escrituras con rol admin (donde aplica).
  - Unicidad de `codigo` en crear/actualizar (409/400 ante duplicado).
  - Bandera `activo` para habilitar/deshabilitar sin borrar (soft toggle).
  - Borrado protegido: se bloquea el DELETE si el registro está en uso (tiene referencias) — devuelve 400.
  - Registros de sistema protegidos que no pueden eliminarse (ej. los 4 canales de venta base: POS, LANDING, WHATSAPP, TELEFONO).
  - Alcance de datos: algunos mantenedores son **tablas maestras globales** (categorías, tipos, unidades) y otros son **por tenant**; la spec distingue ambos casos en lugar de asumir tenant scoping universal.
- Se documenta el **inventario** de mantenedores existentes, distinguiendo los CRUD embebidos en el módulo de las opciones que redirigen a páginas dedicadas (Config. Landing, Usuarios, Tenants).
- No se modifica código existente: es documentación retroactiva del estado actual (baseline). Los mantenedores nuevos se agregarán después como changes que referencian esta spec.

## Capabilities

### New Capabilities
- `mantenedores`: Patrón CRUD compartido de las tablas maestras del backoffice (listar/obtener/crear/actualizar/eliminar), sus reglas transversales (autorización, unicidad de código, bandera `activo`, borrado protegido por uso, registros de sistema, alcance global vs por tenant) e inventario de los mantenedores existentes.

### Modified Capabilities
<!-- Ninguna: es documentación baseline de funcionalidad ya construida. -->

## Impact

- **Nuevo spec**: `openspec/specs/mantenedores/spec.md` (tras archivar este change).
- **Código de referencia (no se modifica)**: `routers/maestras.py`, `routers/canales_venta.py`, `routers/tipos_pedido.py`, `routers/paleta_colores.py`, `routers/locales.py`, y demás routers de tablas maestras en `fme-backend/routers/`.
- **UI de referencia (no se modifica)**: `fme-backoffice/app/admin/mantenedores/` (grilla de opciones + componentes `*List.tsx`).
- Sin migraciones ni cambios de contrato de API. Documentación pura.
