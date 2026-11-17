## ADDED Requirements

### Requirement: Catálogo de módulos
El sistema SHALL definir un catálogo fijo de módulos con códigos estables. El **núcleo** (dashboard, productos, clientes, precios, locales, usuarios y roles, mantenedores generales, alertas) SHALL estar siempre disponible para todo tenant y no SHALL poder contratarse ni quitarse. Los módulos contratables y sus dependencias SHALL ser:

| Código | Módulo | Requiere |
|---|---|---|
| `ventas` | Ventas (pedidos, solicitudes, POS, caja) | — |
| `cotizaciones` | Cotizaciones | `ventas` |
| `preventa` | Pre-venta de cajas | `ventas` |
| `tienda_online` | Tienda online (landing, checkout, pagos en línea) | `ventas` |
| `inventario` | Inventario (stock, movimientos, transferencias, conteos) | — |
| `compras` | Compras (proveedores, facturas, recepción) | `inventario` |
| `produccion` | Producción (recetas, costeo, órdenes de trabajo) | `inventario` |
| `etiquetado` | Etiquetado nutricional | `produccion` |
| `despacho` | Despacho (hojas de ruta, vehículos) | `ventas` |
| `cobranza` | Cobranza (notas de crédito, devoluciones, cheques) | `ventas` |
| `comisiones` | Comisiones de vendedores | `ventas` |
| `fidelizacion` | Fidelización (puntos, enrolamiento) | `ventas` |

Los tenants no SHALL poder crear ni modificar módulos.

#### Scenario: Consulta del catálogo
- **WHEN** un administrador de plataforma consulta el catálogo de módulos
- **THEN** recibe los 12 módulos contratables con su nombre y sus dependencias

### Requirement: Contratación de módulos por tenant
Solo un administrador de plataforma SHALL poder activar o desactivar módulos de un tenant. El sistema SHALL rechazar con HTTP 422 una combinación que no cumpla las dependencias, indicando qué módulo falta o qué módulo depende del que se quiere quitar. Cada cambio SHALL registrar quién lo hizo y cuándo.

#### Scenario: Activar un módulo con su dependencia
- **WHEN** un administrador de plataforma activa `compras` en un tenant que tiene `inventario`
- **THEN** el tenant queda con `compras` contratado

#### Scenario: Activar un módulo sin su dependencia
- **WHEN** un administrador de plataforma activa `etiquetado` en un tenant sin `produccion`
- **THEN** el sistema responde HTTP 422 indicando que falta `produccion`

#### Scenario: Quitar un módulo del que otro depende
- **WHEN** un administrador de plataforma quita `inventario` a un tenant que tiene `compras`
- **THEN** el sistema responde HTTP 422 indicando que `compras` depende de `inventario`

#### Scenario: Usuario de tenant intenta cambiar módulos
- **WHEN** un admin de tenant intenta activar un módulo en su propio tenant
- **THEN** el sistema responde HTTP 403

### Requirement: Bloqueo de APIs de módulos no contratados
Toda operación de la API que pertenezca a un módulo SHALL rechazarse con HTTP 403 y código `modulo_no_contratado` (indicando el módulo) cuando el tenant de la request no lo tiene contratado. El bloqueo SHALL aplicarse aunque el menú esté oculto y también a las requests públicas resueltas por dominio. Las operaciones del núcleo SHALL estar siempre disponibles.

#### Scenario: API de módulo no contratado
- **WHEN** un usuario de un tenant sin `despacho` llama a una API de hojas de ruta
- **THEN** el sistema responde HTTP 403 con código `modulo_no_contratado` y módulo `despacho`

#### Scenario: Tienda online no contratada
- **WHEN** un visitante abre la tienda pública de un tenant sin `tienda_online` y la landing pide el catálogo público
- **THEN** el sistema responde HTTP 403 con código `modulo_no_contratado`

#### Scenario: API del núcleo
- **WHEN** un usuario de un tenant sin módulos contratados consulta sus clientes
- **THEN** el sistema responde normalmente

### Requirement: Menú según módulos contratados
Cada ítem de menú SHALL pertenecer al núcleo o a un módulo. El menú que recibe un usuario SHALL incluir solo ítems del núcleo o de módulos contratados por su tenant, aunque su rol tenga asignados otros. El admin de un tenant SHALL poder asignar a sus roles solo ítems del núcleo o de módulos contratados; un intento de asignar otro ítem SHALL responder HTTP 422.

#### Scenario: Rol con menú de módulo no contratado
- **WHEN** un rol tiene asignado "Despacho" y el tenant no tiene `despacho`
- **THEN** el menú del usuario no incluye "Despacho"

#### Scenario: Asignar menú de módulo no contratado
- **WHEN** el admin de un tenant sin `produccion` asigna "Producción" a un rol
- **THEN** el sistema responde HTTP 422 y el rol no cambia

#### Scenario: Recontratar un módulo
- **WHEN** a un tenant se le quita `despacho` y luego se le vuelve a activar
- **THEN** los roles que tenían "Despacho" asignado lo vuelven a ver sin reasignarlo

### Requirement: Módulos visibles para el tenant
El sistema SHALL informar al usuario autenticado la lista de módulos contratados por su tenant, para que la interfaz oculte lo no contratado.

#### Scenario: Datos del usuario actual
- **WHEN** un usuario consulta sus propios datos
- **THEN** la respuesta incluye la lista de códigos de módulos contratados por su tenant

### Requirement: Continuidad de los tenants existentes
Al introducir los módulos, todo tenant existente SHALL quedar con los 12 módulos contratados, de modo que ningún usuario pierda acceso. Un tenant nuevo SHALL crearse con los módulos que indique el administrador de plataforma (por defecto, ninguno además del núcleo).

#### Scenario: Despliegue sobre tenants existentes
- **WHEN** se aplica la migración en una base con tenants existentes
- **THEN** cada tenant queda con los 12 módulos y su menú no cambia
