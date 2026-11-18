## ADDED Requirements

### Requirement: Envío de eventos a n8n sin afectar la operación
El backend SHALL notificar a n8n los eventos que generan correos al cliente mediante un `POST` JSON a su webhook, en segundo plano y con timeout. Un error de n8n (caído, 4xx/5xx, timeout) SHALL quedar registrado en el log y NO SHALL revertir ni bloquear la operación que lo originó.

#### Scenario: n8n caído al confirmar un pedido
- **WHEN** se confirma un pedido y el webhook de n8n no responde
- **THEN** el pedido queda confirmado igual
- **AND** el backend registra un warning con la URL del webhook

### Requirement: Correo de pedido confirmado
El backend SHALL disparar `pedido-confirmado` cuando un pedido queda confirmado y pagado. Esto ocurre en dos casos: venta del backoffice con pago inmediato, o pago en línea aprobado. El payload SHALL incluir `pedido_id`, `numero_pedido`, `fecha_pedido` (hora de Chile), `monto_total`, datos del cliente, `tenant_nombre`, `items[]`, `seguimiento_url` y `unsub_url`.

#### Scenario: Pago en línea aprobado
- **WHEN** el proveedor confirma el pago en línea de un pedido de la tienda
- **THEN** se dispara `pedido-confirmado` con los ítems del pedido

#### Scenario: Cliente sin correo o que se dio de baja
- **WHEN** el cliente no tiene correo o no acepta el canal email
- **THEN** no se dispara el webhook

#### Scenario: Canal de entrega inmediata
- **WHEN** el pedido es de un canal con entrega inmediata (POS)
- **THEN** no se dispara `pedido-confirmado`

### Requirement: Correo de pedido entregado
El backend SHALL disparar `pedido-entregado` al marcar la entrega en la hoja de ruta, con `numero_pedido`, `fecha_entrega` (hora de Chile), `monto_total`, `cliente_nombre`, `cliente_email` y `unsub_url`, con las mismas guardas de correo y preferencias.

#### Scenario: Entrega registrada
- **WHEN** el repartidor marca como entregado un ítem de la hoja de ruta
- **THEN** se dispara `pedido-entregado` para ese pedido

### Requirement: Correos de cotizaciones
El backend SHALL disparar `cotizacion-creada`, `cotizacion-enviada` (agrega `version_numero`) y `cotizacion-aceptada` (agrega `numero_pedido`, `estado_pedido`, `costo_delivery`, `tiene_delivery`). El payload base SHALL incluir `numero_cotizacion`, `fecha`, `fecha_vencimiento`, `monto_total`, datos del cliente, `tenant_nombre`, `items[]` y `unsub_url`, con las mismas guardas de correo y preferencias.

#### Scenario: Cotización enviada al cliente
- **WHEN** una cotización pasa a ENVIADA y el cliente acepta correos
- **THEN** se dispara `cotizacion-enviada` con la versión activa

### Requirement: Código de verificación del checkout (crítico)
Para verificar el correo del cliente de la tienda, el backend SHALL disparar `verificacion-email` con `email`, `codigo` (6 dígitos), `minutos`, `tienda` y `tienda_url`. El workflow de n8n SHALL enviar el código a ese correo. Como la creación de pedidos de la tienda exige el correo verificado, este workflow SHALL mantenerse activo. En desarrollo el backend SHALL además escribir el código en el log. La URL SHALL poder configurarse con `N8N_WEBHOOK_VERIFICACION_EMAIL`.

#### Scenario: Cliente pide el código
- **WHEN** el cliente de la tienda pide verificar su correo
- **THEN** n8n recibe el payload y envía el código
- **AND** en la base de datos solo queda el HMAC del código

#### Scenario: Workflow desactivado
- **WHEN** el workflow `verificacion-email` no está activo
- **THEN** el webhook responde 404, el backend lo registra y el cliente no recibe el código (no puede crear el pedido)

### Requirement: Flujos de n8n hacia el backend
Los workflows de n8n que llaman al backend SHALL usar endpoints protegidos con `X-API-Key` (`INTEGRATION_API_KEY`) o endpoints públicos de solo lectura. La limpieza nocturna SHALL llamar `DELETE /api/notifications/cleanup`, que elimina las notificaciones leídas de más de 30 días y las no leídas de más de 90.

#### Scenario: Clave inválida
- **WHEN** se llama al endpoint de limpieza sin la API key correcta
- **THEN** el backend responde 401 o 403 y no borra nada

### Requirement: Agente de chat
El workflow "Masas Estación - Agente Chat" (`n26TaZhlycsY7xcA`) SHALL responder consultas de clientes con un modelo de IA y SHALL consultar productos solo mediante el endpoint público de solo lectura `GET /api/productos/catalogo`.

#### Scenario: Pregunta por un producto
- **WHEN** un cliente pregunta por un producto en el chat
- **THEN** el agente consulta el catálogo público y responde sin acceder a datos privados del backend

### Requirement: Todo workflow queda registrado en esta spec
Todo workflow de n8n que FME cree, modifique, desactive o elimine SHALL quedar registrado en esta spec mediante un change de OpenSpec que la modifique (delta ADDED/MODIFIED/REMOVED de `integracion-n8n`). El registro SHALL indicar nombre e ID del workflow, disparador (webhook o cron), dirección (FME → n8n o n8n → FME), contrato del payload o endpoint y si es crítico para la operación. El change SHALL además incluir el export del workflow a `n8n/workflows/`.

#### Scenario: Nuevo workflow de correo
- **WHEN** se crea un workflow nuevo en n8n para FME
- **THEN** el change que lo introduce agrega un requisito en `integracion-n8n` con su contrato
- **AND** agrega su archivo exportado a `n8n/workflows/`

#### Scenario: Workflow eliminado
- **WHEN** se elimina un workflow de FME en n8n
- **THEN** el change lo saca de la spec con un delta REMOVED y lo borra de `n8n/workflows/` (`--podar`)

### Requirement: Workflows versionados en el repositorio
Todo workflow de n8n usado por FME SHALL estar exportado en `n8n/workflows/` de fme-backend, con `scripts/n8n_exportar.py`, en el mismo cambio que lo crea o modifica. Los workflows de otros productos de la misma instancia SHALL listarse en `n8n/excluir.json`. El export SHALL tener formato estable: sin fechas ni identificadores volátiles, con claves ordenadas.

#### Scenario: Workflow nuevo
- **WHEN** se crea un workflow en n8n y se ejecuta el export
- **THEN** aparece un archivo `<nombre>--<id>.json` en `n8n/workflows/` sin necesidad de configurarlo

#### Scenario: Revisión de sincronía
- **WHEN** se ejecuta `scripts/n8n_exportar.py --verificar`
- **THEN** termina con código 1 si algún workflow difiere de lo versionado

### Requirement: Sin secretos en los workflows versionados
El export SHALL reemplazar por `__SECRETO__:<nombre>` cualquier valor escrito en un nodo cuyo nombre parezca una clave: API key, token, authorization, password o secret. Las credenciales de n8n SHALL exportarse solo como referencia `{id, name}`.

#### Scenario: Header con API key escrita a mano
- **WHEN** un nodo HTTP tiene el header `X-API-Key` con su valor real
- **THEN** el archivo exportado contiene `__SECRETO__:X-API-Key` y el script avisa en qué nodo lo ocultó
