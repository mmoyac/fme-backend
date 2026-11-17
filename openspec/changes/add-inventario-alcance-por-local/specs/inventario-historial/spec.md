## ADDED Requirements

### Requirement: Historial limitado al local propio
Para un usuario con local asignado y sin alcance total, el historial SHALL incluir solo movimientos donde su local es origen o destino, aunque pida otro filtro de local; el filtro de local no se muestra.

#### Scenario: Vendedor revisa historial
- **GIVEN** un vendedor de TilTil y movimientos de Lampa, TilTil y entre ambos
- **WHEN** abre Historial
- **THEN** ve solo los movimientos que involucran a TilTil

#### Scenario: Intento de ver otro local
- **WHEN** un vendedor de TilTil consulta el historial filtrando por Lampa vía API
- **THEN** recibe solo movimientos que involucran a TilTil
