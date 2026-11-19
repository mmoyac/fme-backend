# Spec Delta

## ADDED Requirements

### Requirement: Bandeja de despacho con contadores
La portada de Despacho del backoffice SHALL mostrar, para el tenant del usuario, cuatro contadores: *Por despachar* (pedidos despachables y solicitudes con delivery sin hoja de ruta), *Pagados sin confirmar* (pedidos con pago en línea confirmado que siguen en estado PENDIENTE), *En ruta* (hojas de ruta en estado EN_RUTA) y *Entregados hoy* (ítems de hoja de ruta entregados en el día). Al hacer clic en *Por despachar* o *Pagados sin confirmar* la lista SHALL mostrar esos elementos. Los datos de otros tenants MUST NOT incluirse.

#### Scenario: Contadores al abrir Despacho
- **WHEN** un usuario abre `/admin/despacho` y su tenant tiene 3 pedidos despachables sin ruta, 1 pagado sin confirmar y 1 hoja en ruta
- **THEN** los contadores muestran Por despachar 3, Pagados sin confirmar 1 y En ruta 1

#### Scenario: Pedido pagado que no se confirmó solo
- **WHEN** un pedido se pagó en línea pero quedó PENDIENTE porque no se pudo confirmar automáticamente
- **THEN** aparece en *Pagados sin confirmar* con acceso al pedido para confirmarlo

#### Scenario: Aislamiento por tenant
- **WHEN** el tenant A tiene pedidos pendientes de despacho
- **THEN** la bandeja del tenant B no los cuenta ni los lista

### Requirement: Lista de pendientes con comuna y filtros
La bandeja SHALL listar los pendientes de despacho con número, cliente (o locales de origen y destino en solicitudes), dirección, comuna de entrega, fecha, total y si está pagado. SHALL permitir agruparlos por comuna mediante chips con su conteo, incluido un grupo "Sin comuna" para los que no la tienen, y filtrarlos por rango de fechas y por pagado / no pagado.

#### Scenario: Filtrar por comuna
- **WHEN** hay 5 pendientes en Lampa y 3 en Colina y el usuario elige el chip "Lampa (5)"
- **THEN** la lista muestra solo los 5 de Lampa

#### Scenario: Pedido sin comuna
- **WHEN** un pedido despachable no tiene comuna de entrega (ej. creado en el backoffice)
- **THEN** se cuenta y se lista en el grupo "Sin comuna"

### Requirement: Crear hoja de ruta desde la selección
El usuario SHALL poder seleccionar pendientes en la bandeja y crear una hoja de ruta con ellos. El sistema SHALL abrir el formulario de nueva hoja de ruta con esos pendientes ya marcados, manteniendo las validaciones existentes (chofer, vehículo y capacidad en kg).

#### Scenario: Ruta con los pedidos de una comuna
- **WHEN** el usuario filtra "Lampa", marca todos y presiona "Crear hoja de ruta con seleccionados"
- **THEN** se abre "Nueva Hoja de Ruta" con esos pedidos marcados y, al crearla, dejan de aparecer en Por despachar

#### Scenario: Selección que excede la capacidad
- **WHEN** los pedidos seleccionados superan la capacidad del vehículo elegido
- **THEN** el sistema muestra el aviso de capacidad existente y no crea la hoja

### Requirement: Los retiros no son despachables
Un pedido con modalidad de entrega RETIRO MUST NOT aparecer como pendiente de despacho ni como disponible para hoja de ruta, aunque su costo de delivery sea 0. Un pedido es despachable si está CONFIRMADO, no está en ninguna hoja de ruta y tiene modalidad DESPACHO o un costo de delivery mayor que 0.

#### Scenario: Retiro en tienda web
- **WHEN** un pedido web con modalidad RETIRO y costo de delivery 0 queda CONFIRMADO
- **THEN** no aparece en la bandeja ni en los pedidos disponibles para hoja de ruta

#### Scenario: Delivery gratis
- **WHEN** un pedido web con modalidad DESPACHO tiene costo de delivery 0 por superar el monto de envío gratis
- **THEN** sí aparece como pendiente de despacho
