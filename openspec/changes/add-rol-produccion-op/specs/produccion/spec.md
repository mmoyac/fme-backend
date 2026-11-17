# Spec Delta

## Purpose

Gobierna el ciclo de vida de la Orden de Producción (OP): un administrador solicita
qué fabricar y cuánto, y el rol de producción informa lo realmente producido, dejando
trazabilidad de quién pidió, quién produjo y la diferencia entre ambos.

## ADDED Requirements

### Requirement: Rol de producción por tenant

El sistema SHALL disponer de un rol `produccion` en cada tenant, con acceso al menú
Producción del backoffice. Los tenants nuevos y los existentes MUST contar con este rol.

#### Scenario: Tenant existente recibe el rol

- **WHEN** se aplica la migración de este cambio sobre una base con tenants existentes
- **THEN** cada tenant tiene un rol `produccion` con permiso al menú `/admin/produccion`

#### Scenario: Rol no duplicado

- **WHEN** un tenant ya tiene un rol llamado `produccion`
- **THEN** el sistema no crea un segundo rol con ese nombre

### Requirement: Solo administradores solicitan producción

El sistema SHALL permitir crear una OP manualmente (directa o como OT tipo OP) solo a
usuarios con rol administrador (`admin`, `administrador` o `superadmin`). Otros roles
MUST recibir `403`.

#### Scenario: Admin crea OP

- **WHEN** un usuario con rol `admin` hace `POST /api/produccion/ordenes` con detalles válidos
- **THEN** la OP se crea en estado `PLANIFICADA` y `solicitado_por_id` queda con el id del usuario

#### Scenario: Rol produccion intenta crear OP

- **WHEN** un usuario con rol `produccion` hace `POST /api/produccion/ordenes`
- **THEN** el sistema responde `403` y no crea la OP

#### Scenario: Vendedor intenta crear OT tipo OP

- **WHEN** un usuario con rol `vendedor` crea una OT de tipo `OP` vía `POST /api/ordenes-trabajo`
- **THEN** el sistema responde `403` y no crea ni la OT ni la OP

### Requirement: OP generada desde cotización registra solicitante

Las OP creadas automáticamente al aceptar una cotización SHALL seguir creándose sin
restricción de rol y MUST registrar como solicitante al usuario que aceptó la cotización.

#### Scenario: Aceptación de cotización con faltante de stock

- **WHEN** un usuario acepta una cotización que genera una OP automática
- **THEN** la OP se crea con `solicitado_por_id` igual al id de ese usuario

### Requirement: Producción finaliza la OP con lo realmente producido

El sistema SHALL permitir finalizar una OP a usuarios con rol `produccion` o
administrador, informando la cantidad realmente producida por detalle. Otros roles
MUST recibir `403`.

#### Scenario: Producción informa cantidad menor

- **GIVEN** una OP `PLANIFICADA` con un detalle de 4 cajas de empanadas
- **WHEN** un usuario con rol `produccion` la finaliza informando 3 como cantidad producida real
- **THEN** la OP queda `FINALIZADA`, el detalle registra `cantidad_producida = 3`, el inventario
  del producto terminado aumenta en 3 y `producido_por_id` queda con el id del usuario

#### Scenario: Sin ajuste se asume lo programado

- **WHEN** producción finaliza la OP sin informar cantidad real para un detalle
- **THEN** ese detalle registra `cantidad_producida` igual a `cantidad_programada`

#### Scenario: Vendedor intenta finalizar

- **WHEN** un usuario con rol `vendedor` hace `POST /api/produccion/ordenes/{id}/finalizar`
- **THEN** el sistema responde `403` y la OP no cambia

#### Scenario: Cantidad producida negativa

- **WHEN** se informa una cantidad producida real menor que 0
- **THEN** el sistema responde `422` y la OP no cambia

### Requirement: La OP se cierra sin saldo pendiente

Al finalizar, la OP SHALL cerrarse con lo realmente producido aunque sea menor a lo
programado. El sistema MUST NOT crear OP complementarias ni dejar saldo pendiente.

#### Scenario: Producción parcial cierra la OP

- **WHEN** se finaliza una OP de 4 unidades informando 3 producidas
- **THEN** la OP queda `FINALIZADA`, no existe una nueva OP por la unidad faltante y la OT
  vinculada (si existe) queda `CERRADA`

### Requirement: Motivo de diferencia opcional

Al finalizar, el sistema SHALL aceptar un `motivo_diferencia` opcional por detalle y
persistirlo. El motivo no es obligatorio aunque se produzca menos.

#### Scenario: Motivo informado

- **WHEN** producción finaliza informando 3 de 4 con motivo "se rompió una bandeja"
- **THEN** el detalle guarda ese motivo y se devuelve al consultar la OP

#### Scenario: Diferencia sin motivo

- **WHEN** producción finaliza informando 3 de 4 sin motivo
- **THEN** la OP se finaliza igualmente y el motivo queda vacío

### Requirement: Consulta de OP muestra trazabilidad y diferencia

Al listar o consultar OP, el sistema SHALL devolver por OP el solicitante y el productor
(id y nombre/email), y por detalle la cantidad programada, la producida, la diferencia
(producida − programada) y el motivo.

#### Scenario: OP finalizada con faltante

- **WHEN** se consulta `GET /api/produccion/ordenes` y existe una OP finalizada con 3 de 4
- **THEN** su detalle muestra `cantidad_programada = 4`, `cantidad_producida = 3`, `diferencia = -1`
  y la OP muestra quién la solicitó y quién la produjo

#### Scenario: OP planificada

- **WHEN** se consulta una OP aún `PLANIFICADA`
- **THEN** `producido_por` y `diferencia` vienen vacíos

### Requirement: Solo administradores eliminan OP

El sistema SHALL permitir eliminar una OP no finalizada solo a roles administradores.

#### Scenario: Rol produccion intenta eliminar

- **WHEN** un usuario con rol `produccion` hace `DELETE /api/produccion/ordenes/{id}`
- **THEN** el sistema responde `403` y la OP no se elimina

### Requirement: El rol produccion no crea, edita ni cancela Órdenes de Trabajo

El sistema SHALL rechazar con `403` las operaciones de crear (`POST /api/ordenes-trabajo/`), editar (`PUT /api/ordenes-trabajo/{id}`) y cancelar (`POST /api/ordenes-trabajo/{id}/cancelar`) Órdenes de Trabajo de cualquier tipo cuando el usuario tiene rol `produccion`. Ese rol solo finaliza: informa lo producido en las OP y puede avanzar etapas y cerrar OT. El backoffice SHALL ocultarle "+ Nueva OT" y "Cancelar OT", y la página de nueva OT SHALL mostrarle un aviso en lugar del formulario.

#### Scenario: Producción intenta crear una OT de servicio
- **WHEN** un usuario con rol `produccion` hace `POST /api/ordenes-trabajo/` con un tipo de servicio
- **THEN** el sistema responde `403` "Tu rol solo puede finalizar órdenes, no crearlas ni modificarlas" y no crea la OT

#### Scenario: Producción intenta cancelar una OT
- **WHEN** un usuario con rol `produccion` hace `POST /api/ordenes-trabajo/{id}/cancelar`
- **THEN** el sistema responde `403` y la OT no cambia

### Requirement: El admin edita las cantidades de una OP planificada

El sistema SHALL exponer `PUT /api/produccion/ordenes/{id}/cantidades`, solo para roles admin, para cambiar la `cantidad_programada` de una OP PLANIFICADA, sin bajar de lo que necesita el pedido vinculado (cantidad del ítem menos el stock del local). El cambio se refleja en la OT y en su registro de actividad (reunión 16-11-26, punto 1.3.1).

#### Scenario: Producir más de lo pedido
- **WHEN** el admin edita la OP de un pedido de 10 unidades sin stock y programa 30
- **THEN** la OP queda programada en 30, la OT muestra 30 y el registro de actividad dice "10 → 30"

#### Scenario: Programar menos de lo que necesita el pedido
- **WHEN** el admin intenta programar 5 en esa OP
- **THEN** el sistema responde `400` indicando que el pedido necesita al menos 10

#### Scenario: Rol produccion u OP finalizada
- **WHEN** un usuario `produccion` intenta editar, o se intenta editar una OP FINALIZADA
- **THEN** el sistema responde `403` o `400`, respectivamente, y la OP no cambia

### Requirement: Las notas de la cotización llegan a producción

Al aceptar una cotización que genera OT/OP por falta de stock, el sistema SHALL copiar a las notas de la OT y de la OP las notas de la cotización y las de la aceptación. El modal de finalizar la OP SHALL mostrarlas destacadas como "Instrucciones".

#### Scenario: Instrucción para producir extra
- **WHEN** la cotización tiene la nota "producir 30 para stock" y se acepta con faltante
- **THEN** la OP generada muestra esa nota en Producción y en el modal de finalizar
