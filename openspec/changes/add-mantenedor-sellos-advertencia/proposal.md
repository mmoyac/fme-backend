## Why

Los sellos de advertencia (catálogo `sellos_advertencia`: Alto en Calorías, Azúcares, Sodio, Grasas Saturadas, Contiene Edulcorantes, Contiene Cafeína) solo se pueden poblar hoy mediante un script de seed manual (`scripts/seed_sellos_advertencia.py`), y no hay forma de gestionarlos desde el backoffice. En producción esto ya causó que los sellos no aparecieran hasta correr el seed a mano. Se necesita un mantenedor que permita administrar el catálogo desde `/admin/mantenedores`, siguiendo el patrón de mantenedores existente.

## What Changes

- Se agrega el mantenedor **Sellos de Advertencia** al módulo `/admin/mantenedores`, reusando el patrón CRUD compartido documentado en la capability `mantenedores`.
- **Backend**: se agregan endpoints de escritura para el catálogo `sellos_advertencia` (crear, actualizar, eliminar y habilitar/deshabilitar). Hoy solo existe `GET /etiquetas/sellos`.
- **Alcance de datos**: tabla maestra **global** (los sellos chilenos son los mismos para todos los tenants).
- **Registros de sistema**: los 6 sellos base del seed se tratan como registros de sistema (no eliminables; editables con cuidado).
- **Borrado protegido**: no se puede eliminar un sello que esté asignado a productos (`producto_sellos`).
- **Frontend**: nuevo componente `SellosList.tsx` y nueva opción en la grilla de `mantenedores/page.tsx`.
- Se actualiza el **inventario** de la spec `mantenedores` para incluir Sellos de Advertencia.

## Capabilities

### New Capabilities
<!-- Ninguna nueva: reusa el patrón de la capability `mantenedores`. -->

### Modified Capabilities
- `mantenedores`: se agrega el mantenedor de Sellos de Advertencia al inventario y se documentan sus particularidades (catálogo global, registros de sistema del seed, borrado protegido por asignación a productos).

## Impact

- **Backend**: `routers/etiquetas.py` (nuevos endpoints POST/PUT/DELETE para `sellos_advertencia`), `schemas/etiquetas.py` (schemas Create/Update). Modelo `SelloAdvertencia` ya existe.
- **Frontend**: `fme-backoffice/app/admin/mantenedores/components/SellosList.tsx` (nuevo), `mantenedores/page.tsx` (nueva opción), `lib/api/etiquetas.ts` (llamadas CRUD).
- **Dependencia**: este change reusa el patrón de la capability `mantenedores`; conviene archivar antes `document-mantenedores-baseline`.
- Sin migraciones nuevas (la tabla `sellos_advertencia` ya existe). El seed queda como opcional/inicialización.
