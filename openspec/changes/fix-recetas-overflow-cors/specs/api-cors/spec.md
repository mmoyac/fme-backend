## ADDED Requirements

### Requirement: Cabeceras CORS en todas las respuestas, incluidos errores

La API SHALL incluir las cabeceras CORS apropiadas (`Access-Control-Allow-Origin`
y `Access-Control-Allow-Credentials`) en **todas** las respuestas dirigidas a un
origen permitido, incluyendo respuestas de error (`4xx`/`5xx`) y las generadas por
excepciones no controladas. El cliente nunca SHALL recibir un error de red ("Failed
to fetch") en lugar del código y cuerpo de error reales por falta de cabeceras CORS.

#### Scenario: Respuesta exitosa con origen permitido

- **WHEN** un cliente con un `Origin` permitido recibe una respuesta `2xx`
- **THEN** la respuesta incluye `Access-Control-Allow-Origin` con ese origen y
  `Access-Control-Allow-Credentials: true`

#### Scenario: Respuesta de error con origen permitido

- **WHEN** un endpoint lanza una excepción no controlada y responde `500` (u otro
  error) a un cliente con `Origin` permitido
- **THEN** la respuesta de error incluye las cabeceras CORS, de modo que el navegador
  permite leerla y el frontend obtiene el código/cuerpo de error reales

#### Scenario: Preflight de origen permitido

- **WHEN** llega una petición `OPTIONS` (preflight) desde un `Origin` permitido
- **THEN** la API responde `204` con las cabeceras `Access-Control-Allow-*`

#### Scenario: Origen no permitido

- **WHEN** la petición proviene de un `Origin` no permitido
- **THEN** la API no agrega cabeceras CORS de permiso (y el preflight responde `400`)
