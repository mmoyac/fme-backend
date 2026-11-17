# Proposal

## Why

Los usuarios de cada tenant aprenden a usar el sistema de boca en boca o preguntándonos directamente, y cada módulo nuevo que se contrata repite el problema. Necesitamos un centro de capacitación con lecciones interactivas por módulo que solo vean los usuarios autenticados, y solo de los módulos que su tenant tiene contratados. No puede ser un HTML público porque el material describe procesos internos del negocio.

## What Changes

- Nuevo catálogo de lecciones de capacitación, versionado en git dentro de fme-backend y fuera de cualquier carpeta servida públicamente. Lo crea y mantiene el equipo de desarrollo.
- Cada lección es un HTML autocontenido e interactivo (CSS, JS e imágenes embebidas): quizzes, paso a paso, simuladores. Sin videos.
- Cada módulo tiene un manifiesto con el título, la descripción y el orden de sus lecciones. Hay además una sección `general` (uso básico del sistema) visible para cualquier usuario autenticado.
- Nuevos endpoints autenticados en `/api/capacitacion`: índice de lo que el usuario puede ver, y contenido de una lección. Un usuario sin el módulo contratado recibe 403; sin sesión, 401.
- En fme-backoffice: nueva página `/admin/capacitacion` con el índice por módulo y un visor que muestra la lección en un iframe aislado (sandbox sin acceso al origen del backoffice ni al token).

## Capabilities

### New Capabilities
- `capacitacion`: catálogo de lecciones de capacitación por módulo, control de acceso por autenticación y módulo contratado, entrega del contenido y su visualización aislada en el backoffice.

### Modified Capabilities
(ninguna)

## Impact

- **fme-backend**: nuevo router `routers/capacitacion.py`, registrado en `main.py`; nueva carpeta de contenido `capacitacion/` (manifiestos + HTML). Reutiliza `get_current_active_user`, `modulos_de_tenant` y `MODULOS` de `utils/modulos.py`. Sin cambios en la BD ni migraciones.
- **fme-backoffice**: nueva ruta `app/admin/capacitacion/` (índice + visor), cliente API y entrada en el menú.
- **Docker/deploy**: la carpeta `capacitacion/` tiene que quedar dentro de la imagen de fme-backend (revisar `.dockerignore`).
- Sin dependencias nuevas.
