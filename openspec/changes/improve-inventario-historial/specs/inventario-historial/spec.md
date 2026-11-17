## MODIFIED Requirements

### Requirement: Volumen del historial
La consulta del historial SHALL entregarse paginada: cada página trae como máximo 100 movimientos (ajustable hasta 500 por solicitud) y la pestaña SHALL ofrecer "Cargar más" mientras existan movimientos anteriores que cumplan los filtros.

#### Scenario: Más de 100 movimientos
- **GIVEN** el tenant tiene 250 movimientos
- **WHEN** el usuario abre Historial sin filtros
- **THEN** se muestran los 100 más recientes y la opción "Cargar más"

#### Scenario: Cargar más
- **GIVEN** se muestran 100 de 250 movimientos
- **WHEN** el usuario presiona "Cargar más" dos veces
- **THEN** se muestran los 250 movimientos y la opción desaparece

### Requirement: Filtros del historial
El historial SHALL permitir filtrar por producto, por local (movimientos donde el local es origen o destino), por tipo de movimiento y por rango de fechas (desde / hasta, inclusivo, en hora de Chile), combinables entre sí. Cambiar un filtro reinicia la paginación.

#### Scenario: Filtro por local
- **WHEN** el usuario filtra por el local Lampa
- **THEN** solo se muestran movimientos con Lampa como origen o como destino

#### Scenario: Filtro por tipo
- **WHEN** el usuario filtra por tipo "Transferencia"
- **THEN** solo se muestran movimientos `TRANSFERENCIA`

#### Scenario: Filtro por fechas
- **WHEN** el usuario filtra desde el 01-11-2026 hasta el 15-11-2026
- **THEN** solo se muestran movimientos registrados entre esas fechas, ambos días incluidos

### Requirement: Tipos de movimiento
El filtro de tipo SHALL ofrecer los tipos de movimiento efectivamente registrados para productos del tenant. Los tipos conocidos (`TRANSFERENCIA`, `PEDIDO`, `AJUSTE`, `AJUSTE_INVENTARIO`, `MERMA`, `ENTRADA_INICIAL`, `AJUSTE_CONTEO`, `PRODUCCION`, `DEVOLUCION`, `DEVOLUCION_LOTE`, `ENTRADA_ENROLAMIENTO`, `RESERVA_LOTE`, `VENTA_LOTE`, `AJUSTE_RECEPCION`) SHALL mostrarse con etiqueta legible; un tipo desconocido MUST mostrarse con su código tal cual.

#### Scenario: Filtrar por producción
- **GIVEN** existen movimientos `PRODUCCION`
- **WHEN** el usuario abre el filtro de tipo
- **THEN** aparece la opción "Producción" y al elegirla solo se listan esos movimientos

#### Scenario: Tipo sin etiqueta
- **WHEN** existe un movimiento con un tipo no conocido
- **THEN** se lista y aparece en el filtro mostrando su código

## ADDED Requirements

### Requirement: Exportar historial a Excel
El historial SHALL poder descargarse como archivo `.xlsx` aplicando los mismos filtros de la pantalla, con una fila por movimiento (fecha y hora de Chile, tipo, SKU, producto, local origen, local destino, cantidad, usuario, notas) hasta un máximo de 10.000 movimientos; si el resultado supera ese máximo, el archivo MUST indicarlo.

#### Scenario: Exportar con filtros
- **GIVEN** el usuario filtró por local Lampa y tipo Merma
- **WHEN** presiona "Exportar Excel"
- **THEN** descarga un `.xlsx` solo con las mermas que involucran a Lampa

#### Scenario: Aislamiento por tenant en la exportación
- **WHEN** el usuario exporta el historial
- **THEN** el archivo contiene solo movimientos de productos de su tenant
