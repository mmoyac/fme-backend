# Spec Delta

## Purpose

Permite revisar los movimientos de stock del tenant (transferencias, ventas, mermas, producción, ajustes, conteos, etc.) para auditar quién movió qué, cuándo y entre qué locales.

## ADDED Requirements

### Requirement: Listado de movimientos
La pestaña Historial SHALL listar los movimientos de inventario del tenant ordenados del más reciente al más antiguo, mostrando fecha y hora, tipo, producto (nombre y SKU), local de origen, local de destino, cantidad, usuario y notas. Un origen o destino nulo se muestra como "-".

#### Scenario: Movimiento de merma
- **WHEN** existe una merma registrada en Lampa
- **THEN** aparece con tipo "Merma", origen Lampa, destino "-", la cantidad, el usuario y el motivo en notas

### Requirement: Filtros del historial
El historial SHALL permitir filtrar por producto, por local (movimientos donde el local es origen o destino) y por tipo de movimiento, combinables entre sí.

#### Scenario: Filtro por local
- **WHEN** el usuario filtra por el local Lampa
- **THEN** solo se muestran movimientos con Lampa como origen o como destino

#### Scenario: Filtro por tipo
- **WHEN** el usuario filtra por tipo "Transferencia"
- **THEN** solo se muestran movimientos `TRANSFERENCIA`

### Requirement: Tipos de movimiento
El historial SHALL mostrar etiquetas legibles para los tipos `TRANSFERENCIA`, `PEDIDO`, `AJUSTE`, `MERMA`, `ENTRADA_INICIAL` y `AJUSTE_CONTEO`; cualquier otro tipo registrado por el sistema (por ejemplo `PRODUCCION`, `DEVOLUCION`, `ENTRADA_ENROLAMIENTO`, `VENTA_LOTE`) MUST mostrarse con su código tal cual.

#### Scenario: Tipo sin etiqueta
- **WHEN** existe un movimiento `PRODUCCION`
- **THEN** se lista mostrando el tipo "PRODUCCION"

### Requirement: Acceso al conteo desde el historial
Un movimiento `AJUSTE_CONTEO` SHALL ofrecer un enlace "Ver conteo #N" que abre el detalle del conteo de origen en la pestaña Conteo.

#### Scenario: Navegar al conteo
- **WHEN** el usuario hace clic en "Ver conteo #42" de un movimiento de ajuste por conteo
- **THEN** se abre la pestaña Conteo con el detalle del conteo #42

### Requirement: Volumen del historial
La consulta del historial SHALL devolver como máximo los 100 movimientos más recientes que cumplan los filtros.

#### Scenario: Más de 100 movimientos
- **GIVEN** el tenant tiene 250 movimientos
- **WHEN** el usuario abre Historial sin filtros
- **THEN** se muestran los 100 más recientes

### Requirement: Aislamiento por tenant en historial
El historial MUST incluir solo movimientos de productos del tenant del usuario autenticado.

#### Scenario: Movimientos de otro tenant
- **WHEN** otro tenant registra movimientos
- **THEN** no aparecen en el historial del usuario
