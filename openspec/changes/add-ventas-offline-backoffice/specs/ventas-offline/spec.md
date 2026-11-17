## ADDED Requirements

### Requirement: Punto de venta único en el backoffice

El sistema SHALL operar las ventas al mostrador exclusivamente desde `fme-backoffice`
(`/admin/pedidos/pos`), instalable como PWA. La aplicación `fme-pos` (Capacitor) SHALL
considerarse descartada y no SHALL recibir nuevas funcionalidades.

#### Scenario: Instalación en el equipo de caja

- **WHEN** un usuario abre el backoffice en Chrome/Edge del equipo de caja
- **THEN** puede instalarlo como aplicación (PWA) y abrir el POS desde el escritorio

### Requirement: Creación idempotente de ventas

El endpoint `POST /api/pedidos/backoffice` SHALL aceptar un `client_uuid` opcional. Si
ya existe un pedido del mismo tenant con ese `client_uuid`, el sistema SHALL responder
el pedido existente sin crear otro y sin repetir efectos (inventario, puntos, caja).

#### Scenario: Reintento de una venta ya registrada

- **WHEN** el cliente envía dos veces una venta con el mismo `client_uuid`
- **THEN** existe un solo pedido, el inventario se descontó una sola vez y la segunda
  respuesta es 200 con el mismo `pedido_id` y `numero_pedido` y `duplicado: true`

#### Scenario: Envíos simultáneos con el mismo client_uuid

- **WHEN** llegan dos requests concurrentes con el mismo `client_uuid`
- **THEN** solo uno crea el pedido y el otro responde el pedido existente, sin error 500

#### Scenario: Venta sin client_uuid

- **WHEN** un cliente antiguo o una integración envía la venta sin `client_uuid`
- **THEN** el sistema la crea como hasta ahora

### Requirement: Detección de conectividad con la API

El POS SHALL considerar que está "En línea" solo si la API responde. El sistema SHALL
exponer `GET /health` y el POS SHALL usar heartbeat y timeouts para cambiar de
estado.

#### Scenario: API colgada con internet disponible

- **WHEN** el equipo tiene internet pero la API no responde dentro del timeout
- **THEN** el POS pasa a estado "Sin conexión" y permite seguir vendiendo

#### Scenario: Recuperación de la conexión

- **WHEN** el heartbeat responde correctamente dos veces seguidas
- **THEN** el POS pasa a "En línea" e inicia la sincronización de pendientes

### Requirement: Online por defecto con contingencia automática

El POS SHALL operar siempre en línea contra la API. El modo sin conexión SHALL
activarse y desactivarse automáticamente, sin acción del vendedor, y SHALL usarse solo
mientras la API no esté disponible. Una venta en curso NO SHALL interrumpirse ni
perderse por un corte de conexión.

#### Scenario: Corte de internet a mitad de una venta

- **WHEN** el vendedor está armando el carrito y se cae la conexión
- **THEN** el carrito se mantiene intacto, el banner cambia a "Sin conexión" y el
  vendedor puede terminar la venta normalmente

#### Scenario: Corte justo al confirmar la venta

- **WHEN** el vendedor confirma la venta y el envío a la API falla por red o timeout
- **THEN** la venta queda guardada en la cola local, se imprime el comprobante
  provisorio y el vendedor puede atender al siguiente cliente sin reintentar a mano

#### Scenario: Vuelve la conexión

- **WHEN** la API vuelve a responder
- **THEN** el POS vuelve solo a "En línea", las siguientes ventas se registran
  directamente en el servidor y las pendientes se sincronizan en segundo plano

### Requirement: Venta sin conexión

Estando "Sin conexión", el POS SHALL permitir registrar ventas usando el catálogo,
precios, clientes y maestras cacheados localmente, siempre que exista un turno de caja
abierto cacheado. Cada venta SHALL guardarse en una cola local con un `client_uuid`
único y un `numero_provisorio`, y SHALL imprimirse un comprobante provisorio.

#### Scenario: Venta offline exitosa

- **WHEN** el POS está "Sin conexión", hay turno cacheado y el vendedor confirma una venta en efectivo
- **THEN** la venta queda en la cola con estado PENDIENTE, se imprime un comprobante
  provisorio con su `numero_provisorio` y el contador de pendientes aumenta

#### Scenario: Sin turno de caja cacheado

- **WHEN** el POS está "Sin conexión" y no hay turno de caja abierto en la caché
- **THEN** el POS no permite registrar ventas e indica que se debe abrir caja con conexión

#### Scenario: Funcionalidades no disponibles offline

- **WHEN** el POS está "Sin conexión"
- **THEN** no se ofrecen canje de puntos, pago con cheque, medios de pago con
  crédito/plazo ni creación de clientes nuevos, y se ofrece "Consumidor final"

#### Scenario: Apertura del POS sin red

- **WHEN** el usuario abre la PWA sin conexión y ya había usado el POS en ese equipo
- **THEN** el POS carga desde el service worker y la caché local, sin redirigir al login

### Requirement: Sincronización segura de ventas pendientes

El POS SHALL enviar las ventas pendientes en orden FIFO, de a una, reutilizando su
`client_uuid` en cada intento. Errores de red o 5xx SHALL reintentarse con backoff;
errores de negocio (4xx) SHALL dejar la venta en estado CON_ERROR para revisión; un 401
SHALL pausar la sincronización hasta un nuevo login sin perder la cola.

#### Scenario: Sincronización tras reconexión

- **WHEN** vuelve la conexión con 3 ventas PENDIENTE
- **THEN** se crean 3 pedidos en el backend, cada venta pasa a SINCRONIZADA con su
  `numero_pedido` definitivo y el contador vuelve a 0

#### Scenario: Respuesta perdida durante el envío

- **WHEN** el backend creó el pedido pero la respuesta no llegó al POS
- **THEN** el reintento con el mismo `client_uuid` devuelve el pedido existente y no hay duplicado

#### Scenario: Varias pestañas abiertas

- **WHEN** el POS está abierto en dos pestañas del mismo equipo
- **THEN** cada venta pendiente se envía una sola vez

#### Scenario: Sesión vencida

- **WHEN** la sincronización recibe 401
- **THEN** se pausa, se pide iniciar sesión y las ventas pendientes se conservan

### Requirement: Reglas de negocio para ventas sincronizadas desde offline

Una venta con `origen = OFFLINE` representa una transacción ya realizada. El backend
SHALL registrarla aunque el stock sea insuficiente o el precio haya cambiado,
conservando el precio cobrado, su `fecha_venta_cliente` y su `turno_caja_id`, y SHALL
generar alertas para revisión.

#### Scenario: Stock insuficiente al sincronizar

- **WHEN** se sincroniza una venta OFFLINE de un producto sin stock suficiente
- **THEN** el pedido se crea, el inventario puede quedar negativo y se genera una alerta

#### Scenario: Precio cambiado al sincronizar

- **WHEN** el precio vigente difiere del precio cobrado offline
- **THEN** el pedido se registra con el precio cobrado y queda marcado `diferencia_precio`

#### Scenario: Turno ya cerrado al sincronizar

- **WHEN** la venta OFFLINE referencia un turno de caja que ya fue cerrado
- **THEN** se registra como ajuste post-cierre de ese turno y se alerta al administrador

### Requirement: Protección de ventas no sincronizadas

El POS SHALL impedir acciones que puedan perder ventas pendientes del equipo.

#### Scenario: Cerrar turno con pendientes

- **WHEN** el vendedor intenta cerrar el turno con ventas PENDIENTE o CON_ERROR en el equipo
- **THEN** el sistema lo impide e indica que primero debe sincronizar o resolver errores

#### Scenario: Logout con pendientes

- **WHEN** el usuario intenta cerrar sesión con ventas pendientes
- **THEN** el sistema advierte y no cierra la sesión hasta sincronizar

#### Scenario: Revisión de ventas pendientes

- **WHEN** el usuario abre "Ventas pendientes"
- **THEN** ve cada venta con su estado, número provisorio, monto, error (si hay) y puede reintentar
