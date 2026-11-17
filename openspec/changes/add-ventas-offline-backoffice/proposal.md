## Why

Los usuarios reportan que el sistema es **inestable**: cuando la API no responde (caída
de red del local, API colgada como en el incidente del 2026-11-11, latencia alta) el
punto de venta queda bloqueado y no se puede vender. Para una panadería/tienda eso es
pérdida directa de ventas y filas en el mesón.

Además, el flujo actual tiene un riesgo latente: `POST /api/pedidos/backoffice` **no es
idempotente**. Si la respuesta se pierde por un corte y el vendedor reintenta, se crea
una venta duplicada (doble descuento de inventario, doble suma de puntos, doble monto
en caja).

## Decisión de arquitectura: ventas solo desde fme-backoffice

- **Se descarta `fme-pos`** (Next.js + Capacitor, APK Android). No se evoluciona ni se
  le aplican cambios; queda como repositorio inactivo.
- **El módulo de ventas se opera exclusivamente desde `fme-backoffice`**, pantalla
  `/admin/pedidos/pos` (producción: https://admin.masasestacion.cl/admin/pedidos/pos;
  código: `fme-backoffice/app/admin/pedidos/pos/page.tsx`).
- El backoffice **ya es una PWA** (`@ducanh2912/next-pwa`, `public/sw.js`,
  `app/manifest.ts`), por lo que se puede instalar en el PC/tablet de caja y abrir sin
  conexión. Lo que falta es la capa de **datos offline** (catálogo local + cola de
  ventas pendientes + sincronización), que es el objeto de este change.

## What Changes

- **Backend (fme-backend)**
  - `POST /api/pedidos/backoffice` acepta un `client_uuid` (generado por el cliente) y
    pasa a ser **idempotente**: si ya existe un pedido con ese `client_uuid` en el
    tenant, devuelve el pedido existente sin volver a crearlo.
  - Nuevos campos opcionales en la venta: `fecha_venta_cliente` (momento real de la
    venta), `origen` (`ONLINE` / `OFFLINE`), `turno_caja_id` (turno con el que se
    vendió) y `numero_provisorio` (el impreso en el comprobante offline).
  - Reglas de sincronización para ventas ya realizadas: no se rechazan por stock
    insuficiente ni por diferencia de precio; se registran y se alertan.
  - Endpoint liviano de salud (`GET /health`) para detectar conectividad real.
- **Frontend (fme-backoffice)**
  - Detección de conectividad por *heartbeat* + *timeouts* (no confiar solo en
    `navigator.onLine`).
  - Caché local (IndexedDB) de los datos que necesita la pantalla POS.
  - Cola local (*outbox*) de ventas, con envío FIFO, reintentos y el mismo
    `client_uuid` en cada intento.
  - Indicador de estado (En línea / Sin conexión / Sincronizando N) y pantalla de
    "Ventas pendientes" con errores y reintento manual.
  - Comprobante provisorio impreso cuando la venta se hace offline.
- **Alcance offline acotado** (lo demás sigue requiriendo conexión): venta al
  mostrador con medios de pago inmediatos, cliente "consumidor final" o cliente ya
  cacheado, sin canje de puntos, sin cheques, sin crédito/plazo, sin crear clientes.

## Capabilities

### New Capabilities

- `ventas-offline`: operar el punto de venta del backoffice sin conexión al servidor
  y sincronizar las ventas de forma segura (sin duplicados) cuando vuelve la conexión.

### Modified Capabilities

- (ninguna spec base existente de pedidos/ventas; se documenta todo en `ventas-offline`)

## Impact

- **fme-backend**: `routers/pedidos.py` (`crear_pedido_backoffice`), schema
  `PedidoCreateBackoffice`, modelo `Pedido` + migración Alembic (columnas nuevas e
  índice único `(tenant_id, client_uuid)`), router de salud.
- **fme-backoffice**: `app/admin/pedidos/pos/page.tsx`, `lib/api/pedidos.ts`, nuevo
  `lib/offline/*` (db, outbox, sync, conectividad), layout admin (no expulsar al
  usuario por error de red), configuración PWA (`next.config.js`).
- **fme-pos**: ninguno (descartado).
- **Tributario**: sin impacto. Todas las ventas pasan por el POS de Transbank, que emite
  el documento tributario; el ticket del sistema es solo un comprobante interno.
