## Context

El módulo de Mantenedores es la pantalla `/admin/mantenedores` del backoffice, que agrupa ~20 tablas maestras del sistema. La UI es una grilla de opciones (`app/admin/mantenedores/page.tsx`) donde cada opción renderiza un componente `*List.tsx` con CRUD, o redirige a una página dedicada. La lógica de negocio real vive en el backend (FastAPI), principalmente en `routers/maestras.py` y routers específicos (`canales_venta.py`, `tipos_pedido.py`, `paleta_colores.py`, `locales.py`, etc.).

Al haberse construido con vibe coding, el patrón está implementado de forma consistente pero no documentado. Esta spec es **documentación retroactiva** (baseline) del comportamiento observado en el código, no un rediseño.

## Goals / Non-Goals

**Goals:**
- Capturar el patrón CRUD compartido y las reglas transversales que cualquier mantenedor debe cumplir.
- Servir de contrato para agregar mantenedores nuevos vía OpenSpec changes, reusando el patrón.
- Dejar un inventario del estado actual (qué mantenedores existen y cómo se sirven).

**Non-Goals:**
- No se refactoriza ni cambia código existente.
- No se unifican las variaciones actuales (p. ej. algunos routers usan `get_current_active_user` para escrituras y otros `get_current_admin_user`); se documentan como están.
- No se especifica la UI a nivel de componentes; el foco es el contrato de comportamiento (mayormente API backend).
- No se cubren las páginas dedicadas (Usuarios, Tenants, Config. Landing) más allá de listarlas como parte del inventario; tienen sus propias specs.

## Decisions

**1. Una sola capability `mantenedores` (patrón + inventario) en lugar de una por tabla.**
Los ~20 mantenedores comparten el mismo patrón CRUD. Documentar cada uno como capability separada generaría 20 archivos casi idénticos y difíciles de mantener. En su lugar, la spec describe el patrón como requisitos con escenarios, y adjunta un inventario. Alternativa descartada: spec monolítica con cada tabla detallada (grande, redundante).

**2. La spec vive en `fme-backend`.**
La convención del proyecto es que la spec va en el repo dueño de la lógica. El CRUD real (endpoints, validaciones, guards de borrado, alcance de datos) está en el backend; la UI del backoffice es un cliente de esos endpoints. Alternativa descartada: duplicar en `fme-backoffice` (que además no tiene OpenSpec inicializado).

**3. Documentar variaciones reales en vez de normalizar.**
El código tiene variaciones legítimas: tablas globales vs por tenant, autorización admin vs usuario activo, y guards de borrado distintos. La spec captura el patrón base y marca explícitamente las variaciones permitidas, para no mentir sobre el estado actual ni forzar un refactor no pedido.

**4. Registros de sistema protegidos como requisito de primera clase.**
Casos como los 4 canales de venta base (POS, LANDING, WHATSAPP, TELEFONO) que no pueden eliminarse son parte del patrón y se especifican como escenario, no como excepción anecdótica.

## Risks / Trade-offs

- [La spec baseline puede divergir del código con el tiempo] → Al agregar cada mantenedor nuevo como change, actualizar el inventario en la spec `mantenedores` en el mismo change.
- [Documentar variaciones en lugar de normalizar puede perpetuar inconsistencias (auth admin vs activo)] → Se acepta como deuda conocida; si más adelante se decide unificar, será un change explícito con su propio proposal.
- [El inventario listado puede quedar incompleto si hay mantenedores fuera de la grilla] → El inventario se ancla a las opciones de `page.tsx` como fuente de verdad de la UI; cualquier tabla maestra sin entrada en esa grilla queda fuera de alcance de esta spec.

## Migration Plan

No aplica (documentación). Al archivar el change, el delta se fusiona en `openspec/specs/mantenedores/spec.md`.
