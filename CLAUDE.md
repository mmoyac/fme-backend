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
