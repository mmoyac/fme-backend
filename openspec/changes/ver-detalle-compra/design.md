## Context

El backoffice (`fme-backoffice`, Next.js App Router) tiene en `app/admin/compras/`:
- `page.tsx`: lista de compras. Para RECIBIDA solo muestra el texto "Procesada".
- `[id]/page.tsx`: pantalla de **edición**, que para RECIBIDA hace alert + redirect.
- `nuevo/page.tsx`: alta.

El backend `GET /api/compras/{id}` ya devuelve cabecera + `detalles` para cualquier
estado, y existe `getCompra(id)` en `lib/api/compras.ts`. Falta exclusivamente una
vista de lectura y su acceso.

## Goals / Non-Goals

**Goals:**
- Ver el detalle de cualquier compra (PENDIENTE o RECIBIDA) en solo lectura.
- Acceso directo desde la lista mediante un enlace "Ver".

**Non-Goals:**
- No se agrega edición de compras recibidas (sigue prohibida).
- No se cambia el backend.
- No se agrega exportación/PDF (queda fuera de alcance).

## Decisions

- **Ruta nueva `app/admin/compras/[id]/detalle/page.tsx`**: vista de solo lectura.
  Se elige una ruta separada en vez de un modo "view" dentro de `[id]/page.tsx` para
  no mezclar la lógica de edición (que bloquea RECIBIDA) con la de lectura, y mantener
  cada página simple. Alternativa descartada: parámetro `?view=1` en la página de
  edición — complica el control de estado del formulario.
- **Enlace "Ver" en la lista**: se muestra para todas las compras; en RECIBIDA
  reemplaza el texto "Procesada". Reutiliza `getCompra(id)` y los mapas de proveedores/
  locales ya disponibles para resolver nombres.
- **Resolución de nombres** (producto, proveedor, local, tipo doc): la vista carga los
  catálogos como ya hace la página de edición, para mostrar nombres en vez de IDs.

## Risks / Trade-offs

- [Duplicación parcial de la tabla de detalle entre edición y vista] → Aceptable; la
  vista es más simple (sin acciones) y evita condicionar el formulario de edición.
- [Carga de catálogos solo para nombres] → Igual patrón que la página de edición; el
  costo es bajo y consistente con el resto del módulo.
