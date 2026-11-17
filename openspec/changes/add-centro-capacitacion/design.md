# Design

## Context

- La autenticación es JWT Bearer. El backoffice guarda el token en `localStorage` (`fme_auth_token`) y lo envía en el header `Authorization`. Un recurso pedido directo por el navegador (`<a href>`, `<iframe src>`, `<img src>`) **no lleva ese header**, así que no se puede proteger con la auth actual.
- Ya existen los bloques de control de acceso por módulo: `MODULOS`, `modulos_de_tenant(db, tenant_id)` y `_tenant_de_request(request, db)` en `utils/modulos.py`, que resuelve el tenant considerando la impersonación del superadmin. `require_modulo(m)` sirve para un módulo fijo por router, pero aquí el módulo viene en la URL.
- `/app/static` se publica con nginx: el contenido de capacitación **no** puede vivir ahí.
- La imagen se arma con `COPY . .` y `.dockerignore` no excluye carpetas nuevas, así que `capacitacion/` entra a la imagen sin cambios.
- Regla del proyecto (incidente 2026-11-11): endpoints con BD síncrona siempre con `def`, nunca `async def`.

## Goals / Non-Goals

**Goals:**
- Que agregar una lección sea solo agregar un archivo HTML más una línea en un manifiesto, con commit y deploy normales.
- Que el JS de la lección corra pero no pueda leer la sesión ni actuar como el usuario.

**Non-Goals:**
- Seguimiento de avance, puntajes o "lección vista" (los quizzes evalúan solo en el navegador y no guardan nada).
- Edición desde el backoffice, contenido por tenant y videos.
- Búsqueda de texto dentro de las lecciones.

## Decisions

### D1. Contenido en archivos dentro de fme-backend, no en la BD
Estructura:
```
capacitacion/
  _plantilla.html            # base con estilos y componentes (quiz, pasos) para copiar
  general/
    manifest.json
    primeros-pasos.html
  inventario/
    manifest.json
    01-stock-por-local.html
    ...
```
`manifest.json`: `{"lecciones": [{"slug": "...", "titulo": "...", "descripcion": "...", "archivo": "01-stock-por-local.html"}]}`. El orden del arreglo es el orden de presentación.

- **Por qué:** lo mantiene el equipo, queda versionado y revisable en PR, y no requiere migraciones ni un editor.
- **Alternativa descartada:** tabla en BD con editor. Sirve cuando edita alguien no técnico, que no es el caso. Si cambia, se migra detrás del mismo API sin tocar el frontend.

### D2. El módulo de la URL se valida contra `MODULOS` + `general`, y el archivo solo se resuelve desde el manifiesto
El endpoint nunca arma la ruta con lo que llega en la URL. Primero valida que `modulo` esté en `MODULOS ∪ {"general"}` y que `slug` cumpla con `^[a-z0-9_-]+$`. Después busca el slug en el manifiesto ya cargado y lee el `archivo` declarado ahí, verificando que la ruta resuelta quede dentro de `capacitacion/<modulo>/`. Así se elimina el path traversal por construcción.

### D3. Manifiestos cargados al iniciar, con caché en memoria
Un servicio `services/capacitacion_service.py` carga y valida todos los manifiestos al primer uso (con `lru_cache`): JSON válido, slugs únicos que cumplan el patrón y archivos existentes. Un manifiesto inválido se registra en el log y su sección se omite, sin botar la API. El HTML se lee en cada request: son archivos chicos y así no se infla la memoria.
- Como el contenido cambia solo con deploy, la caché nunca queda obsoleta en prod. En local, reiniciar el contenedor recarga los manifiestos.

### D4. Endpoints
Router `routers/capacitacion.py`, montado en `/api/capacitacion` con `Depends(get_current_active_user)` a nivel router (sin `require_modulo`, porque el módulo es dinámico):
- `GET /api/capacitacion` → `{"secciones": [{"modulo", "nombre", "lecciones": [{"slug", "titulo", "descripcion"}]}]}`. `general` va primero y después los módulos en el orden de `MODULOS`.
- `GET /api/capacitacion/{modulo}/{slug}` → `text/html; charset=utf-8`, con headers `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`.

Visibilidad: `tenant_id = _tenant_de_request(request, db)`. Si es `None` y el usuario es superadmin, ve todo. Si no, ve `general ∪ modulos_de_tenant(db, tenant_id)`. Se expone `_tenant_de_request` como función pública (`tenant_de_request`) en vez de importar un nombre privado. Todo con `def` síncrono.

### D5. Visor: fetch autenticado + `<iframe srcdoc sandbox="allow-scripts">`
El backoffice pide el HTML con el cliente API (que agrega el Bearer) y lo inyecta en `srcdoc` de un iframe con `sandbox="allow-scripts"`, **sin** `allow-same-origin`. Así el documento queda en un origen opaco: su JS corre, pero no ve `localStorage`, cookies ni `window.parent.document`, y un `fetch` a la API sale sin credenciales.
- **Alternativa descartada:** `iframe src` a una URL con token en query string. El token queda en logs de nginx, en el historial y en headers Referer.
- **Alternativa descartada:** inyectar el HTML directo en el DOM (`dangerouslySetInnerHTML`). Los `<script>` no se ejecutan y, si se forzara, tendrían acceso total a la sesión.
- Alto del iframe: la lección envía `parent.postMessage({tipo: "capacitacion:alto", alto})` (incluido en la plantilla). El visor acepta solo mensajes cuyo `event.source` sea su iframe y usa ese alto con un mínimo y un máximo. Si no llega el mensaje, usa un alto fijo con scroll interno.

### D6. Lecciones autocontenidas a partir de una plantilla
Todo inline: CSS, JS e imágenes (SVG inline o `data:` URI). No se cargan recursos externos, porque el sandbox con origen opaco igual lo permitiría y no queremos dependencias de CDN ni filtrar información. `_plantilla.html` trae la paleta del backoffice, un componente de quiz, un paso a paso con avance y el script de alto. Las lecciones se escriben a partir de ella para que se vean uniformes.

### D7. Backoffice
- `app/admin/capacitacion/page.tsx`: índice con una tarjeta por sección y sus lecciones.
- `app/admin/capacitacion/[modulo]/[slug]/page.tsx`: visor, con navegación anterior/siguiente según el índice.
- `lib/api/capacitacion.ts`: `getIndice()` y `getLeccion(modulo, slug)` (devuelve texto).
- Acceso "🎓 Capacitación" en la barra superior (`TopBar.tsx`, junto a la campana de notificaciones), siempre visible para todos los usuarios autenticados; no es un ítem del menú lateral (que viene de la BD por rol). `/admin/capacitacion` se permite a todos los roles en `app/admin/layout.tsx`. La ruta no se mapea en `moduloDeRuta`, porque el filtrado lo hace la API.

### D8. La capacitación se mantiene en el mismo change que modifica el módulo
Regla del proyecto: todo cambio en el comportamiento, los flujos o las pantallas de un módulo actualiza sus lecciones en el mismo change o PR (editar, crear, quitar y actualizar la fecha de revisión). Se hace cumplir por tres vías:
- `openspec/config.yaml` (`rules.proposal` y `rules.tasks`): OpenSpec exige declarar las lecciones afectadas en Impact y un grupo de tareas "Actualizar capacitación".
- `CLAUDE.md` de fme-backend y fme-backoffice: la misma regla para cualquier cambio, use OpenSpec o no.
- Cada lección muestra "Última revisión: AAAA-MM-DD" en su encabezado, para que se note cuando quedó desfasada.

### D9. Primer contenido: módulo Inventario
Las lecciones salen de las capabilities documentadas en `document-inventario-baseline`: existencias y alertas, merma, historial de movimientos, transferencias directas y solicitudes de transferencia. El conteo de inventario (`add-conteo-inventario`) se agrega cuando ese change esté implementado. Stock de cajas pertenece al módulo `preventa` y queda para su propia sección.

## Risks / Trade-offs

- [Una lección mal escrita (JS roto) se ve mal] → Se revisa en PR y se prueba en local. El sandbox evita que afecte al resto del backoffice.
- [Un usuario puede copiar o imprimir el contenido después de verlo] → Es aceptable: el objetivo es que no sea público, no hacer DRM.
- [Lecciones grandes con imágenes en base64 hacen pesada la respuesta] → Preferir SVG y capturas comprimidas. Límite orientativo de 2 MB por lección, que el servicio advierte en el log.
- [El contenido queda desactualizado respecto a las pantallas] → Cada lección indica en su encabezado la fecha de última revisión, y los changes que modifican pantallas de un módulo revisan su capacitación.

## Migration Plan

Sin migraciones de BD. Deploy normal (push a main). Rollback: revertir el commit, ya que no hay datos persistidos.
