Las instrucciones están en Agent.md

## Reglas de eficiencia (minimizar tokens)

- Antes de leer un archivo, usar Grep para ubicar exactamente las líneas relevantes.
- Leer archivos siempre con offset/limit. Nunca leer un archivo completo si supera 150 líneas.
- Para buscar dónde está algo, usar Grep o Glob en lugar de leer directorios completos.
- No leer un archivo solo para confirmar algo que ya está en el contexto de la conversación.
- Hacer múltiples búsquedas en paralelo cuando no hay dependencias entre ellas.
