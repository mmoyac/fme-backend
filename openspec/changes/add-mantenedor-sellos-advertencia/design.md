## Context

El catálogo de sellos vive en la tabla `sellos_advertencia` (modelo `SelloAdvertencia`: `codigo`, `nombre`, `descripcion`, `color`, `icono`, `orden`, `activo`). La relación con productos es `producto_sellos` (`ProductoSello`). Hoy `routers/etiquetas.py` solo expone `GET /etiquetas/sellos` (lista los `activo == True` ordenados por `orden`) y endpoints para asignar sellos a un producto. No hay CRUD del catálogo en sí, por lo que la única forma de poblarlo es el seed manual.

## Goals / Non-Goals

**Goals:**
- Gestionar el catálogo de sellos desde el backoffice (crear/editar/eliminar/activar) siguiendo el patrón de mantenedores.
- Evitar depender del seed manual en producción.

**Non-Goals:**
- No se cambia cómo se asignan sellos a productos (eso ya funciona).
- No se calculan sellos automáticamente desde la info nutricional.
- No se agrega alcance por tenant (el catálogo es global).

## Decisions

**1. Reusar el patrón `mantenedores`, no crear capability nueva.**
Coherente con la decisión de la spec base: un mantenedor nuevo es una instancia del patrón. El delta va como requirement ADDED dentro de la capability `mantenedores`.

**2. Catálogo global.**
Los sellos de la ley de etiquetado chilena son universales; se mantienen como tabla maestra global (sin `tenant_id`), igual que categorías/tipos/unidades.

**3. Los 6 sellos del seed son registros de sistema.**
No se pueden eliminar (protección de sistema). Se pueden editar campos presentacionales (`nombre`, `descripcion`, `color`, `icono`, `orden`, `activo`) pero el `codigo` de un sello de sistema no debería cambiar. El seed se conserva como inicialización idempotente (ya aborta si existe algún sello).

**4. Borrado protegido por asignación.**
No se elimina un sello referenciado en `producto_sellos`; se responde 400. Para "sacar de circulación" un sello se usa `activo = false`.

## Risks / Trade-offs

- [Editar un sello de sistema podría romper la presentación de etiquetas ya impresas] → Restringir edición del `codigo` en sellos de sistema; permitir solo campos presentacionales.
- [Eliminar un sello asignado dejaría etiquetas inconsistentes] → Guard de borrado por `producto_sellos` + preferencia por `activo=false`.
- [Este change depende de la spec base] → Archivar `document-mantenedores-baseline` antes de aplicar este.

## Migration Plan

- Sin migración de esquema (la tabla ya existe).
- Al desplegar, el catálogo puede quedar vacío en instancias nuevas: el mantenedor permite poblarlo desde la UI, y el seed sigue disponible como atajo.
