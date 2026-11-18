Las instrucciones están en Agent.md

## Reglas de eficiencia (minimizar tokens)

- Antes de leer un archivo, usar Grep para ubicar exactamente las líneas relevantes.
- Leer archivos siempre con offset/limit. Nunca leer un archivo completo si supera 150 líneas.
- Para buscar dónde está algo, usar Grep o Glob en lugar de leer directorios completos.
- No leer un archivo solo para confirmar algo que ya está en el contexto de la conversación.
- Hacer múltiples búsquedas en paralelo cuando no hay dependencias entre ellas.

## Regla: el Centro de Capacitación sigue al módulo

- El contenido de capacitación vive en `fme-backend/capacitacion/<modulo>/` (manifest.json + lecciones HTML).
- **Todo cambio que modifique el comportamiento, los flujos o las pantallas de un módulo (ej. inventario) DEBE actualizar en el mismo change/PR las lecciones de ese módulo**: editar las afectadas, crear las nuevas, quitar las obsoletas y actualizar la fecha de última revisión.
- Si el módulo todavía no tiene lecciones, dejarlo anotado en el change como pendiente.
- Un change de OpenSpec que toca un módulo con lecciones no está terminado sin su grupo de tareas "Actualizar capacitación".

## Regla: los workflows de n8n viven en este repo

- Todo workflow de n8n que use FME (creado o modificado, por la UI, el MCP `n8n-effi4tech` o la API) DEBE exportarse a `n8n/workflows/` en el mismo cambio, con `python scripts/n8n_exportar.py` (o `--podar` si se eliminó alguno), y commitearse.
- Nunca dejar claves en los nodos del JSON: el export las reemplaza por `__SECRETO__:<nombre>`, pero revisa el aviso que imprime. Ver `n8n/README.md`.
- Workflows de otros productos del mismo n8n van en `n8n/excluir.json`.
- Todo workflow nuevo, modificado, desactivado o eliminado DEBE quedar registrado en la spec `integracion-n8n` (`openspec/specs/integracion-n8n/spec.md`) mediante un change de OpenSpec con su delta: nombre, ID, disparador, dirección, contrato del payload y si es crítico. Ver las reglas en `openspec/config.yaml`.

## Regla: listados sin consultas por registro (N+1)

- En endpoints que devuelven listas, no acceder a relaciones lazy ni hacer `db.query(...)` dentro del bucle por cada registro. Cargar relaciones con `joinedload` (muchos-a-uno) o `selectinload` (colecciones; `joinedload` en colecciones multiplica filas) y, para datos de otra tabla, una sola consulta con `in_(ids)` armada en un dict.
- Un GET de listado nunca escribe en la BD.
- Verificar contando consultas (event `before_cursor_execute` del engine) y comparando la respuesta con la versión anterior. Ver `openspec/changes/fix-n1-listados/`.
