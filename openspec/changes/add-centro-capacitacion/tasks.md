# Tasks

## 1. Catálogo y servicio (fme-backend)

- [x] 1.1 Crear `capacitacion/` con `general/manifest.json` e `inventario/manifest.json` (vacíos o con una lección de prueba) y verificar que la carpeta no esté excluida en `.dockerignore` ni quede bajo `/app/static`
- [x] 1.2 Crear `services/capacitacion_service.py`: carga con caché de manifiestos, validación (JSON, slugs `^[a-z0-9_-]+$` únicos, archivo existente dentro de la carpeta del módulo, advertencia en log si pesa más de 2 MB), `secciones_visibles(modulos | None)` y `leer_leccion(modulo, slug)`. Verificar con tests unitarios: manifiesto inválido omitido sin excepción, slug con `..` rechazado, archivo fuera de la carpeta rechazado y orden respetado
- [x] 1.3 Exponer `tenant_de_request` como función pública en `utils/modulos.py` (dejando `_tenant_de_request` como alias) y verificar que `require_modulo` siga funcionando con los tests existentes de módulos

## 2. API (fme-backend)

- [x] 2.1 Crear `routers/capacitacion.py` con `GET /api/capacitacion` y `GET /api/capacitacion/{modulo}/{slug}` (`def` síncrono, `HTMLResponse` con `Cache-Control: no-store` y `X-Content-Type-Options: nosniff`), y registrarlo en `main.py` con `Depends(get_current_active_user)`
- [x] 2.2 Tests de API para los escenarios de la spec: 401 sin token, índice con/sin `inventario`, módulo contratado sin lecciones omitido, `general` siempre visible, 403 por módulo no contratado, 404 por slug inexistente/módulo desconocido/traversal, superadmin sin tenant ve todo. Verificar corriéndolos en el contenedor fme-backend (si TestClient sigue roto, verificar con curl contra la API local y dejarlo anotado). Hecho: `tests/test_capacitacion.py` llama al router directo (TestClient roto); 401 sin token y con token inválido verificado contra la API local desde el contenedor

## 3. Plantilla de lecciones

- [x] 3.1 Crear `capacitacion/_plantilla.html`: paleta del backoffice, encabezado con "Última revisión", componentes de quiz (opción múltiple con feedback), paso a paso con avance y tarjeta de tip/advertencia, y script de alto por `postMessage` (`capacitacion:alto`). Verificar abriéndola directo en el navegador sin errores de consola y sin recursos externos. Hecho: paleta oscura del backoffice (slate-900/800, primary); alto calculado con el alto del body para que el iframe también se achique

## 4. Visor e índice (fme-backoffice)

- [x] 4.1 Crear `lib/api/capacitacion.ts` (`getIndice`, `getLeccion` que devuelve texto) con el cliente autenticado existente
- [x] 4.2 Crear `app/admin/capacitacion/page.tsx` (índice por sección con tarjetas de lecciones) y verificar en local con un usuario de tenant 1. Verificado (ver 7.1)
- [x] 4.3 Crear `app/admin/capacitacion/[modulo]/[slug]/page.tsx`: iframe `srcdoc` con `sandbox="allow-scripts"` (sin `allow-same-origin`), ajuste de alto solo para mensajes de su propio iframe, navegación anterior/siguiente y mensaje para 403/404. Verificar que el quiz de prueba funciona y que `localStorage` lanza un error de seguridad desde la consola del iframe. Verificado (ver 7.1)
- [x] 4.4 Agregar el acceso "🎓 Capacitación" en la barra superior (`components/layout/TopBar.tsx`, junto a la campana), no en el menú lateral, y permitir `/admin/capacitacion` a todos los roles en `app/admin/layout.tsx`. Verificar que aparece con y sin módulos contratados y con roles no admin. Verificado (ver 7.1)

## 5. Contenido inicial: Inventario

Las lecciones se ajustaron a las pantallas actuales (relevamiento del backoffice 2026-11-17): se sumaron Conteo (`add-conteo-inventario` ya implementado) y Valorización, que ya son pestañas del módulo.

- [x] 5.1 `inventario/01-existencias-y-alertas.html`: pestañas del módulo, stock por producto y local, local WEB consolidado, semáforo (simulador), filtros, Alertas de Stock del Dashboard y alcance por local. Con quiz
- [x] 5.2 `inventario/02-registrar-merma.html`: paso a paso, formulario de práctica con las validaciones reales y efecto en stock e historial. Con quiz
- [x] 5.3 `inventario/03-transferencias-directas.html`: directa vs solicitud, paso a paso y simulador de stock origen/destino con validaciones. Con quiz
- [x] 5.4 `inventario/04-solicitudes-de-transferencia.html`: diagrama interactivo de estados (qué hace origen y destino en cada uno), crear, atender, finalizar y recepción. Con quiz
- [x] 5.5 `inventario/05-conteo-de-inventario.html`: completo/parcial, contar, diferencias, finalizar/cancelar, Excel y simulador de un conteo. Con quiz
- [x] 5.6 `inventario/06-historial-de-movimientos.html`: tipos de movimiento, filtros, trazabilidad y ejercicio interactivo para identificar el tipo. Con quiz
- [x] 5.7 `inventario/07-valorizacion.html`: totales, valores netos, calculadora por fila, avisos Sin costo/Sin precio. Con quiz
- [x] 5.8 `general/primeros-pasos.html`: login, menú, barra superior, local asignado (no se cambia desde la sesión), módulos del plan y dónde está la capacitación
- [ ] 5.9 Revisar cada lección contra las pantallas reales en local (textos, nombres de botones, flujos) y verificar que se ven completas en el visor. Registradas en los manifiestos en orden; verificado en Chrome headless: sin errores de consola, sin recursos externos

## 6. Regla de mantenimiento

- [x] 6.1 Agregar `rules.proposal` y `rules.tasks` en `openspec/config.yaml` exigiendo actualizar la capacitación del módulo afectado. Verificado: `openspec instructions tasks` devuelve la regla
- [x] 6.2 Documentar la regla "el Centro de Capacitación sigue al módulo" en `CLAUDE.md` de fme-backend y fme-backoffice
- [x] 6.3 Agregar a `add-conteo-inventario` (y a los changes de inventario abiertos que cambian pantallas: `improve-inventario-existencias`, `improve-inventario-historial`, `improve-solicitudes-transferencia`, `add-inventario-alcance-por-local`, `add-valorizacion-inventario`) un grupo "Actualizar capacitación" con las lecciones afectadas. Verificar con `openspec validate` en cada uno. Hecho: agregado a improve-inventario-existencias, improve-inventario-historial, improve-solicitudes-transferencia, add-valorizacion-inventario y fix-inventario-movimientos-trazabilidad (conteo y alcance-por-local ya están implementados y las lecciones los reflejan); todos validan

## 7. Integración

- [x] 7.1 Prueba de punta a punta en local: usuario de tenant con inventario ve y completa las lecciones; usuario de tenant sin inventario no ve la sección y recibe 403 por URL directa; sin sesión, redirige al login. Verificado con `fme-backoffice/e2e/capacitacion.spec.ts` (build de producción, 7/7): índice con General e Inventario; visor con `sandbox="allow-scripts"`, quiz que responde, `localStorage` y `parent.document` dan SecurityError, alto ajustado y navegación a la siguiente; 403 muestra "no disponible en tu plan" sin iframe (403 simulado en el navegador; el 403 real del backend está en `tests/test_capacitacion.py`); 404 con mensaje; 🎓 en la barra superior; rol produccion entra sin redirección; sin sesión → login
