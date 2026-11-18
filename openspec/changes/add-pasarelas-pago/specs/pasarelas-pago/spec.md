## ADDED Requirements

### Requirement: Pasarelas de pago configurables por tenant
El sistema SHALL permitir a un administrador del tenant crear pasarelas de pago (Mercado Pago, Flow, Khipu y, solo en desarrollo, Simulada) con nombre visible, ambiente (INTEGRACION o PRODUCCION) y orden. Las credenciales SHALL guardarse cifradas (AES-256-GCM atado a tenant y pasarela) y NUNCA devolverse por la API.

#### Scenario: Credenciales de solo escritura
- **WHEN** el administrador carga las credenciales de una pasarela
- **THEN** la API responde solo `credenciales_cargadas = true`, la pasarela queda inactiva y exige una nueva prueba

#### Scenario: Activar en producción
- **WHEN** se intenta activar una pasarela de ambiente PRODUCCION sin una prueba de conexión exitosa posterior al último cambio de credenciales
- **THEN** el sistema responde 422 y no la activa

#### Scenario: Pasarela de integración en producción
- **WHEN** el backend corre en producción y una pasarela INTEGRACION o Simulada está activa
- **THEN** no se ofrece al cliente ni puede cobrar

### Requirement: Pago en línea de un pedido de la tienda
Tras crear el pedido, la landing SHALL poder iniciar su pago con una pasarela disponible presentando `pedido_id` y `token_seguimiento`. El monto SHALL fijarlo el backend desde el pedido. La intención SHALL vencer a los 15 minutos.

#### Scenario: Iniciar pago
- **WHEN** la landing envía un pedido pendiente y no pagado con su token y una pasarela disponible
- **THEN** el sistema crea la intención, la registra en el proveedor y devuelve la redirección

#### Scenario: Token inválido o pedido pagado
- **WHEN** el token no corresponde al pedido o el pedido ya está pagado o cancelado
- **THEN** el sistema responde 404 o 400 sin contactar al proveedor

### Requirement: El resultado lo decide el backend consultando al proveedor
El retorno del navegador y la notificación del proveedor SHALL solo identificar la transacción; el backend SHALL consultar el estado al proveedor con sus credenciales antes de registrar nada. Un identificador desconocido SHALL no generar llamadas al proveedor.

#### Scenario: Aviso manipulado
- **WHEN** llega un retorno o webhook con parámetros que dicen "aprobado" pero el proveedor informa otra cosa
- **THEN** se registra lo que informa el proveedor

#### Scenario: Retorno y notificación simultáneos
- **WHEN** el retorno, la notificación y la conciliación procesan el mismo pago aprobado
- **THEN** el pedido queda pagado una sola vez

### Requirement: Casos que requieren revisión
El sistema SHALL dejar la intención EN_REVISION, sin aplicar el pago al pedido, cuando el monto confirmado difiere del de la intención o cuando el pedido ya estaba pagado o cancelado.

#### Scenario: Pago duplicado
- **WHEN** se aprueba un pago de un pedido que ya estaba pagado
- **THEN** la intención queda EN_REVISION con su motivo y el administrador la ve en el listado de pagos

### Requirement: Conciliación periódica
El sistema SHALL consultar cada 2 minutos las intenciones INICIADO de más de 5 minutos y las EXPIRADO de las últimas 24 horas, registrando los aprobados cuyo aviso no llegó.

#### Scenario: Aviso perdido
- **WHEN** el proveedor aprobó un pago pero su notificación nunca llegó
- **THEN** la conciliación lo registra y el pedido queda pagado

### Requirement: Confirmación automática del pedido pagado
Cuando un pago en línea queda aprobado y aplicado, el sistema SHALL confirmar el pedido igual que la confirmación manual del backoffice: local de despacho por defecto del tipo de pedido, descuento de inventario, puntos ganados y estado CONFIRMADO. No SHALL volver a descontar puntos usados (la landing ya los aplicó al crear el pedido). Si no puede confirmarlo (sin local por defecto, stock insuficiente), el pedido SHALL quedar pagado y PENDIENTE y se SHALL notificar a los admins del tenant.

#### Scenario: Stock suficiente
- **WHEN** se aprueba el pago de un pedido cuyo local de despacho por defecto tiene stock
- **THEN** el pedido queda CONFIRMADO, con el inventario descontado y el correo de confirmación enviado

#### Scenario: Stock insuficiente en el local de despacho
- **WHEN** se aprueba el pago pero el local de despacho por defecto no tiene stock suficiente
- **THEN** el pedido queda pagado y PENDIENTE
- **AND** cada admin del tenant recibe la notificación "Pedido X pagado: confirmar manualmente" con el motivo

### Requirement: Notificaciones de pagos que requieren acción
El sistema SHALL notificar en la campana del backoffice a los admins del tenant cuando un pago en línea queda EN_REVISION o cuando un pedido pagado no se pudo confirmar automáticamente.

#### Scenario: Pago duplicado
- **WHEN** un pago se aprueba para un pedido que ya estaba pagado
- **THEN** la intención queda EN_REVISION y los admins reciben "Pago en línea en revisión: pedido X"

### Requirement: Configuración por tenant desde el backoffice
Las pasarelas SHALL configurarse por tenant en Mantenedores → Pasarelas de pago (rol admin, módulo `tienda_online`). El superadmin SHALL configurar las de un tenant operando dentro de él (switch-tenant). Sin tenant en contexto, la API SHALL responder 400.

#### Scenario: Superadmin configura un tenant
- **WHEN** el superadmin entra a un tenant con "Operar en tenant" y crea una pasarela
- **THEN** la pasarela queda asociada a ese tenant
