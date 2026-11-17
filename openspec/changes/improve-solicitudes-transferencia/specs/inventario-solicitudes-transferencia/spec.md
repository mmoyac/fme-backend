## MODIFIED Requirements

### Requirement: Crear solicitud entre locales
Un usuario SHALL poder crear una solicitud con una nota opcional y una lista de productos con cantidad solicitada mayor a 0 (hasta 3 decimales), donde el local que pide (destino) es su local por defecto y el local que despacha (origen) se elige entre los demás locales del tenant, excluyendo el local WEB. El sistema MUST rechazar con 400 una solicitud sin productos, con productos repetidos o con origen igual a destino, y con 404 productos o locales de otro tenant. La solicitud nace en estado `PENDIENTE` y notifica al local origen.

#### Scenario: Solicitud creada
- **GIVEN** un usuario con local por defecto TilTil
- **WHEN** solicita 10 unidades de un producto a Lampa
- **THEN** existe una solicitud `PENDIENTE` con destino TilTil, origen Lampa y el usuario como solicitante, y Lampa recibe una notificación

#### Scenario: Origen igual a destino
- **WHEN** el usuario crea una solicitud con el mismo local como origen y destino
- **THEN** el sistema responde 400 y no crea la solicitud

#### Scenario: Cantidad con decimales
- **WHEN** el usuario solicita 2,5 kg de un producto
- **THEN** la solicitud guarda 2,5 como cantidad solicitada

### Requirement: Finalizar mueve stock
Al pasar de EN_PROCESO a FINALIZADO, el sistema SHALL registrar la cantidad aprobada de cada producto y, por cada producto con cantidad aprobada mayor a 0, descontarla del local origen, sumarla al local destino y registrar un movimiento `TRANSFERENCIA` que referencia la solicitud y al usuario finalizador, todo en una sola operación protegida contra ejecuciones simultáneas. Si algún producto no tiene stock suficiente en el origen, el sistema MUST rechazar la finalización completa con 400 indicando el producto, sin mover stock.

#### Scenario: Finalizar con aprobación parcial
- **GIVEN** una solicitud EN_PROCESO de 10 unidades y stock 20 en el origen
- **WHEN** el origen finaliza aprobando 8
- **THEN** el origen baja 8, el destino sube 8 y existe un movimiento `TRANSFERENCIA` de 8 con referencia a la solicitud y el nombre del usuario

#### Scenario: Stock insuficiente al finalizar
- **GIVEN** stock 5 en el origen
- **WHEN** el origen intenta finalizar aprobando 8 de ese producto
- **THEN** el sistema responde 400 indicando el producto, la solicitud sigue EN_PROCESO y ningún stock cambia

### Requirement: Registrar recepción
Con la solicitud FINALIZADA, el local destino (o un admin) SHALL poder registrar la cantidad recibida de cada producto; si lo recibido difiere de lo aprobado, la diferencia se devuelve al origen o se descuenta del destino según corresponda y cada ajuste MUST registrarse como movimiento `AJUSTE_RECEPCION` con referencia a la solicitud y al usuario. Queda registrado quién recibió y cuándo, y se muestra en el detalle.

#### Scenario: Recepción con faltante
- **GIVEN** una solicitud finalizada con 8 aprobadas
- **WHEN** el destino registra 7 recibidas
- **THEN** el origen recupera 1, el destino queda con 1 menos, existe un movimiento `AJUSTE_RECEPCION` de 1 y el detalle muestra quién recibió y cuándo

## ADDED Requirements

### Requirement: Eliminación solo en estado pendiente
Una solicitud SHALL poder eliminarse solo mientras está `PENDIENTE`; en otro estado el sistema MUST responder 409 y la UI MUST NOT ofrecer la acción.

#### Scenario: Eliminar solicitud en proceso
- **WHEN** el solicitante intenta eliminar una solicitud EN_PROCESO
- **THEN** el sistema responde 409 y la solicitud se mantiene

### Requirement: Pantalla de solicitudes fluida
La pantalla de solicitudes MUST permanecer usable mientras carga datos o genera documentos: el catálogo de productos se carga una sola vez por sesión de pantalla y sin imágenes, la consulta de stock al editar se agrupa en una sola petición tras dejar de escribir, y la generación del PDF no bloquea la interacción. La UI SHALL mostrar solo las acciones que el backend permite al usuario, considerando el rol admin.

#### Scenario: Escribir cantidades
- **WHEN** el usuario edita las cantidades de una solicitud con 10 productos
- **THEN** la pantalla responde sin pausas y se hace como máximo una consulta de stock por pausa de escritura

#### Scenario: Admin ve sus acciones
- **WHEN** un admin sin local por defecto abre una solicitud PENDIENTE
- **THEN** ve la acción "Comenzar atención"
