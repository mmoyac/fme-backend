## ADDED Requirements

### Requirement: Creación de pedido desde el checkout con medio de pago
El endpoint `POST /api/pedidos/` SHALL crear un pedido a partir de los datos del checkout, aceptando opcionalmente un `medio_pago_codigo`. El comportamiento ante un medio de pago válido (incluido `MERCADOPAGO`) SHALL ser equivalente al flujo sin medio de pago ("coordinado"): si los datos son válidos, el pedido se crea y se devuelve la confirmación con `pedido_id` y `numero_pedido`.

#### Scenario: Pedido con Mercado Pago se crea correctamente
- **WHEN** el frontend envía un pedido válido con `medio_pago_codigo = "MERCADOPAGO"`
- **THEN** el sistema crea el pedido en estado PENDIENTE asociando el medio de pago
- **AND** responde 201 con `pedido_id`, `numero_pedido` y `monto_total`

#### Scenario: Medio de pago inexistente
- **WHEN** el frontend envía un `medio_pago_codigo` que no existe en los datos maestros
- **THEN** el sistema responde 400 con un mensaje que identifica el medio de pago no encontrado
- **AND** NO responde 500 ni "Error interno del servidor"

### Requirement: Procesamiento de pago con Mercado Pago
El endpoint `POST /api/payments/process_payment` SHALL procesar el pago enviado por el Payment Brick y reflejar el resultado en el pedido referenciado por `external_reference`.

#### Scenario: Pago aprobado
- **WHEN** Mercado Pago aprueba el pago (`status = "approved"`)
- **THEN** el sistema marca el pedido como pagado, lo deja en estado CONFIRMADO y dispara la notificación de confirmación
- **AND** devuelve el resultado del pago al frontend

#### Scenario: Pago rechazado o pendiente
- **WHEN** Mercado Pago devuelve un estado distinto de `approved` (rechazado, pendiente, en proceso)
- **THEN** el sistema devuelve ese estado al frontend sin marcar el pedido como pagado
- **AND** la respuesta permite al frontend mostrar un mensaje accionable al cliente

### Requirement: Reporte de errores accionable en el flujo de pago
Los endpoints del flujo de checkout (`POST /api/pedidos/`, `POST /api/payments/process_payment`, `POST /api/payments/create_preference/{pedido_id}`) SHALL distinguir errores de validación/negocio de errores inesperados. Los errores esperados SHALL devolverse como respuestas 4xx con un `detail` específico y comprensible. Las excepciones inesperadas SHALL registrarse con contexto (pedido / external_reference, medio de pago) y NO SHALL exponer el mensaje genérico "Error interno del servidor" como única información cuando la causa es conocida y comunicable.

#### Scenario: Error de configuración de Mercado Pago
- **WHEN** el token `MP_ACCESS_TOKEN` no está configurado o Mercado Pago rechaza la solicitud por configuración
- **THEN** el sistema registra el detalle en el log con contexto
- **AND** devuelve un error con `detail` que identifica la causa (configuración de pago), no un 500 genérico opaco

#### Scenario: Excepción inesperada queda trazada
- **WHEN** ocurre una excepción no anticipada durante la creación del pedido o el procesamiento del pago
- **THEN** el sistema registra el traceback completo con el `pedido_id` / `external_reference` asociado
- **AND** el cliente recibe una respuesta de error que no pierde la trazabilidad hacia el log correspondiente

### Requirement: Despliegue del error real en el checkout del cliente
El checkout del frontend SHALL mostrar al cliente el `detail` devuelto por el backend en lugar de un mensaje genérico fijo, y SHALL manejar de forma diferenciada los estados de pago aprobado, rechazado y pendiente.

#### Scenario: El cliente ve el motivo del fallo
- **WHEN** el backend responde con un error de negocio (4xx) durante el checkout
- **THEN** el checkout muestra el `detail` del backend al cliente
- **AND** NO reemplaza el mensaje por un texto genérico que oculte la causa

#### Scenario: Pago no aprobado
- **WHEN** el resultado del pago es rechazado o pendiente
- **THEN** el checkout informa al cliente el estado correspondiente y la acción esperada (reintentar / esperar confirmación)
