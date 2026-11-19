# Spec Delta

## ADDED Requirements

### Requirement: Control manual de impresión de etiquetas de la OP

El sistema SHALL permitir marcar manualmente una OP `FINALIZADA` como "etiquetas impresas", registrando fecha/hora y usuario. Generar o imprimir el PDF de etiquetas MUST NOT marcar la OP por sí solo.

#### Scenario: Marcar etiquetas como impresas

- **WHEN** un usuario con rol producción o admin llama `POST /produccion/ordenes/{id}/etiquetas-impresas` sobre una OP `FINALIZADA` de su tenant
- **THEN** la OP queda con `etiquetas_impresas_at` = ahora y `etiquetas_impresas_por` = ese usuario

#### Scenario: OP no finalizada

- **WHEN** se intenta marcar una OP que no está `FINALIZADA`
- **THEN** el sistema responde `400` y no modifica la OP

#### Scenario: Desmarcar solo admin

- **WHEN** un admin llama `DELETE /produccion/ordenes/{id}/etiquetas-impresas`
- **THEN** la OP vuelve a quedar con etiquetas pendientes
- **AND** un usuario sin rol admin recibe `403`

#### Scenario: Listado informa el estado

- **WHEN** se consulta `GET /produccion/ordenes`
- **THEN** cada OP incluye `etiquetas_impresas_at` y `etiquetas_impresas_por` (null si está pendiente)
