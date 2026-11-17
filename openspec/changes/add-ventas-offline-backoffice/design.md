## Context

- POS actual: `fme-backoffice/app/admin/pedidos/pos/page.tsx` (~1.100 líneas). Llama
  en línea a: catálogo (`/api/productos/catalogo`, `/catalogo-local/{local}`), precios,
  clientes, locales, medios de pago, unidades, canales de venta, tipos de documento,
  caja abierta del local, estimación de puntos y finalmente `crearPedido` →
  `POST /api/pedidos/backoffice`.
- El backend en `crear_pedido_backoffice` (`routers/pedidos.py`): valida cliente,
  local, medio de pago y productos; calcula total; aplica puntos; valida crédito si es
  pago diferido; genera `numero_pedido` correlativo por tenant; exige turno de caja
  abierto en el local; descuenta inventario; registra puntos. **Sin idempotencia.**
- El backoffice ya es PWA (next-pwa con `cacheOnFrontEndNav`,
  `aggressiveFrontEndNavCaching`, `reloadOnOnline`).
- Decisión: **fme-pos (Capacitor) queda descartado**; todo se hace en fme-backoffice.

## Goals / Non-Goals

**Principio rector: online siempre, offline solo como contingencia.**
El POS trabaja normalmente en línea contra la API. El modo sin conexión **no es un modo
de trabajo alternativo** ni algo que el vendedor active: es un respaldo automático que
entra solo cuando se cae internet o la API, para que **la venta en curso no se
interrumpa**, y sale solo cuando vuelve la conexión, sincronizando lo pendiente.

**Goals**
1. Que el vendedor pueda **seguir vendiendo** si la API no responde o no hay internet,
   sin perder el carrito en curso ni tener que hacer nada distinto.
2. **Cero ventas duplicadas** y **cero ventas perdidas** al sincronizar.
3. Que la caja cuadre: toda venta offline termina asociada al turno correcto.
4. Que la mejora de idempotencia beneficie también al modo online (reintentos seguros).

**Non-Goals**
- Offline para el resto del backoffice (inventario, compras, cobranza, reportes, etc.).
- Abrir o cerrar turno de caja sin conexión.
- Canje de puntos, cheques, crédito/plazo, creación de clientes nuevos offline.
- Emisión de documento tributario electrónico (SII) sin conexión.
- Sincronización bidireccional de catálogo editado offline (el catálogo es solo lectura).

## Decisions

### D1. PWA en el backoffice, no app nativa
Se reutiliza la PWA existente. Se instala desde Chrome/Edge en el equipo de caja.
Alternativa descartada: fme-pos con Capacitor (doble código, builds APK, decisión del
negocio de no usarlo).

### D2. Conectividad = "la API responde", no "hay wifi"
`navigator.onLine` dice `true` aunque la API esté colgada. Se usa:
- *Heartbeat* `GET /health` cada 15 s con timeout de 3 s.
- Todas las llamadas del POS con timeout (8 s). Un timeout o error de red pasa el POS
  a modo **Sin conexión** inmediatamente.
- Se vuelve a **En línea** tras 2 heartbeats exitosos seguidos (evita "parpadeo").

### D3. Caché local en IndexedDB
Librería `idb` (≈1 KB) sobre IndexedDB. Stores:
| Store | Contenido | Se refresca |
|---|---|---|
| `catalogo` | catálogo del local con precio vigente, unidad, imagen_url | al entrar al POS online + cada 30 min |
| `clientes` | clientes del tenant (id, nombre, rut, datos tributarios) | ídem |
| `maestras` | medios de pago, tipos documento, canales de venta, unidades | ídem |
| `contexto` | local seleccionado, turno de caja activo, usuario, `device_id` | al abrir turno / login |
| `outbox` | ventas pendientes de sincronizar | ver D4 |
| `meta` | fecha de última actualización de cada store | — |

Se solicita `navigator.storage.persist()` para evitar que el navegador borre los datos.
Si el catálogo cacheado tiene más de 24 h se muestra advertencia (pero se permite vender).

### D4. Outbox de ventas con `client_uuid`
Toda venta del POS (online u offline) se crea así:
1. Se genera `client_uuid = crypto.randomUUID()` y se guarda en `outbox` con estado
   `PENDIENTE`, el payload completo, `fecha_venta_cliente`, `turno_caja_id`,
   `numero_provisorio` y `intentos = 0`.
2. Si está En línea se envía de inmediato; si responde OK pasa a `SINCRONIZADA` (se
   guarda `pedido_id` y `numero_pedido`) y se imprime el comprobante normal.
3. Si falla por red/timeout queda `PENDIENTE` y se imprime **comprobante provisorio**
   con `numero_provisorio`.
4. Si el servidor responde 4xx de negocio queda `CON_ERROR` con el mensaje (no se
   reintenta automáticamente; requiere revisión).

Así hay un solo camino de código para venta online y offline.

`numero_provisorio` = `OFF-{local_id}-{device_id corto}-{correlativo local}`; único por
dispositivo y legible para el cliente.

### D5. Sincronización
- Disparadores: paso a En línea, cada 60 s mientras haya pendientes, botón manual.
- Envío **secuencial FIFO** (una venta a la vez) para respetar el orden de stock y
  correlativos. Un solo "sincronizador" activo por pestaña (lock con
  `navigator.locks`) para que dos pestañas no envíen lo mismo.
- Reintento con backoff (5 s, 15 s, 60 s, máx. 5 min) solo para errores de red/5xx.
- Siempre se reenvía con el **mismo `client_uuid`** → el backend garantiza no duplicar.
- JWT vencido (401): se pausa la sincronización, se pide re-login, la cola se conserva.
- Las ventas `SINCRONIZADA` se purgan del outbox a los 7 días.

### D6. Idempotencia en backend
- Columna `pedidos.client_uuid UUID NULL` + índice único parcial
  `(tenant_id, client_uuid) WHERE client_uuid IS NOT NULL`.
- Al inicio de `crear_pedido_backoffice`: si viene `client_uuid` y ya existe → responder
  **200** con el mismo cuerpo que la creación original (`pedido_id`, `numero_pedido`,
  `monto_total`, `estado`) y `duplicado: true`. Sin efectos secundarios.
- Carrera (dos requests simultáneos): el `IntegrityError` del índice único se captura,
  se hace rollback y se devuelve el pedido existente.
- Recordar regla del proyecto: endpoint `def` síncrono (no `async def`) con BD síncrona.

### D7. Reglas de negocio al sincronizar una venta OFFLINE
La venta **ya ocurrió** (el cliente se fue con el producto y pagó), por eso:
| Situación al sincronizar | Comportamiento |
|---|---|
| Stock insuficiente | Se acepta; inventario puede quedar negativo; se genera alerta de stock negativo |
| Precio cambió desde que se cacheó | Se respeta el precio cobrado (el del payload); se marca `diferencia_precio` |
| Producto desactivado | Se acepta igual (existía al momento de la venta) |
| Turno de caja ya cerrado | Ver D8 |
| Cliente inexistente | `CON_ERROR` (no debería pasar: solo clientes cacheados o consumidor final) |
| Medio de pago no permitido offline | Imposible: la UI lo bloquea; backend lo rechaza con 422 si llega |

`numero_pedido` definitivo lo asigna el backend al sincronizar (correlativo normal).
`fecha_venta_cliente` se guarda aparte; reportes de ventas por día deben usar
`COALESCE(fecha_venta_cliente, fecha_creacion)`.

### D8. Turno de caja
- Solo se puede vender offline si hay un **turno abierto cacheado** (abierto en línea
  previamente). Sin turno cacheado → el POS offline no permite vender.
- La venta lleva `turno_caja_id`; el backend la asocia a ese turno aunque el pedido
  llegue más tarde.
- **Cerrar turno requiere conexión y outbox vacío** (sin `PENDIENTE` ni `CON_ERROR`)
  en ese dispositivo. Esta validación es del cliente porque el backend no conoce la cola
  local. Como respaldo (p. ej. otro equipo cerró el turno), el backend acepta ventas
  OFFLINE para un turno cerrado registrándolas como **ajuste post-cierre** con alerta
  al administrador.

### D9. Experiencia de usuario
- Banner superior permanente en el POS: 🟢 En línea · 🟠 Sin conexión — las ventas se
  guardan en este equipo · 🔵 Sincronizando 3 ventas.
- Contador de pendientes y acceso a "Ventas pendientes" (lista, estado, error, botón
  reintentar, botón ver comprobante).
- En modo Sin conexión se ocultan/deshabilitan: canje de puntos, cheques, medios con
  crédito, crear cliente; el selector de cliente ofrece "Consumidor final" + cacheados.
- Puntos ganados: se calculan en el servidor al sincronizar (el comprobante provisorio
  no los muestra).
- Logout bloqueado (con aviso) si hay ventas pendientes en el equipo.
- El layout admin no debe expulsar al login por error de red; solo por 401 explícito.

### D9b. Comprobante y pago
- El documento tributario lo emite siempre el **POS de Transbank**; el sistema imprime
  solo un **comprobante interno**. Offline el comprobante lleva `numero_provisorio` y
  la leyenda "Comprobante interno – pendiente de sincronizar"; no se reimprime al
  sincronizar.
- Medios de pago habilitados offline: efectivo y tarjeta (cobrada en el terminal
  Transbank). Deshabilitados: cheque y medios con crédito/plazo interno.

### D10. Service worker
- Asegurar que `/admin/pedidos/pos` y sus chunks queden en precache / caché de
  navegación, y que el POS cargue en frío sin red (probar con DevTools → Offline).
- Imágenes de productos: estrategia `CacheFirst` con expiración (no críticas).
- Las llamadas a la API **no** se cachean en el SW (la caché de datos es IndexedDB, D3),
  para no servir respuestas viejas de forma silenciosa.

## Risks / Trade-offs

- **Datos en el navegador se pueden perder** (borrar historial, otro perfil, equipo
  dañado) → `storage.persist()`, sincronizar apenas haya red, bloquear logout con
  pendientes, mostrar contador visible.
- **Stock negativo** temporal en ventas offline → aceptado por negocio; alertas.
- **Precios desactualizados** en caché → refresco periódico y advertencia >24 h.
- **Venta en dos equipos del mismo producto escaso** → mismo caso de stock negativo.
- **Tamaño de catálogo/clientes**: si los clientes son miles, cachear solo campos
  mínimos; revisar volumen real en producción.

## Migration Plan

1. **Fase 1 – Resiliencia (rápida, sin offline aún)**: backend idempotente +
   `GET /health` + timeouts y reintento con `client_uuid` en el POS. Ya elimina
   duplicados y las pantallas colgadas.
2. **Fase 2 – Offline**: IndexedDB, outbox, sincronizador, banner, comprobante
   provisorio, restricciones de alcance.
3. **Fase 3 – Operación**: pantalla de pendientes/errores, reglas de cierre de turno,
   alertas (stock negativo, ajuste post-cierre, diferencia de precio), reportes con
   `fecha_venta_cliente`.

Cada fase es desplegable sola (push a `main`). Rollback: los campos nuevos son
opcionales; el cliente viejo sigue funcionando sin `client_uuid`.

## Open Questions

1. ~~Boleta electrónica SII offline~~ **RESUELTA (2026-11-15)**: todas las ventas pasan
   por el POS de Transbank, que emite el documento tributario. El ticket del sistema es
   **solo un comprobante interno** (no tributario), online u offline. No hay
   implicancia SII en el modo sin conexión.
2. ~~Medios de pago offline~~ **RESUELTA en lo principal**: el cobro con tarjeta lo hace
   el terminal Transbank, independiente del sistema. Offline se permiten los medios
   inmediatos (efectivo y tarjeta vía Transbank); nunca cheque ni crédito interno.
   *Pendiente menor*: confirmar que el terminal Transbank del local tiene conectividad
   propia (SIM/red) y no depende del mismo internet que se cae.
3. **Tiempo máximo offline** aceptable antes de bloquear la venta (¿8 h? ¿un turno?).
4. **Volumen**: cantidad de productos y clientes por tenant para dimensionar la caché.
5. ¿Un turno de caja puede tener **más de un equipo** vendiendo simultáneamente?
