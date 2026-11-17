## 0. Decisión de arquitectura

- [ ] 0.1 Marcar `fme-pos` como descartado (nota al inicio de su README: "Repositorio inactivo; ventas se operan desde fme-backoffice")
- [x] 0.2 SII offline resuelto: Transbank emite el documento tributario; el sistema solo entrega comprobante interno
- [ ] 0.3 Confirmar que el terminal Transbank de cada local tiene conectividad propia (no depende del internet del local)

## 1. Fase 1 – Resiliencia e idempotencia

### Backend (fme-backend)
- [x] 1.1 Migración `a9b8c7d6e5f4`: columnas `client_uuid` (varchar 36), `fecha_venta_cliente`, `origen` (default 'ONLINE'), `turno_caja_id` (FK SET NULL), `numero_provisorio`, `diferencia_precio`; índice único `(tenant_id, client_uuid)` (en PostgreSQL los NULL no colisionan). Probada upgrade/downgrade en BD local
- [x] 1.2 Agregar campos opcionales a `PedidoCreateBackoffice` (`client_uuid` validado como UUID)
- [x] 1.3 En `crear_pedido_backoffice`: búsqueda previa por `client_uuid` → 200 con pedido existente y `duplicado: true`
- [x] 1.4 Capturar `IntegrityError` en el flush del pedido (carrera) → rollback y devolver pedido existente
- [x] 1.5 ~~Endpoint nuevo~~ Se reutiliza `GET /health` existente en `main.py` (sin auth, sin BD)
- [x] 1.6 `scripts/test_idempotencia_pedido_backoffice.py` (corre en transacción revertida): 2 envíos con el mismo `client_uuid` → 1 pedido, 1 descuento de stock, 2ª respuesta 200 `duplicado: true`. Verificado OK en BD local
- [x] 1.6b El pedido POS registra `turno_caja_id` del turno abierto

### Frontend (fme-backoffice)
- [x] 1.7 `lib/net.ts`: `fetchConTimeout` (8 s), `ErrorDeRed`/`ErrorSesion`, `generarUUID`. Aplicado a: venta, tipos de documento del POS, `/users/me` y `/auth/menu`. *(Las cargas de catálogo/clientes del POS se migran en Fase 2 al leerse desde caché)*
- [x] 1.8 `crearPedido` envía `client_uuid` (uno por venta, se mantiene en reintentos mientras no cambie carrito/cliente/pago), timeout 12 s y 1 reintento automático ante red/5xx
- [x] 1.9 `AuthProvider` y layout admin: ante red/timeout/5xx usan usuario y menú en caché en vez de cerrar sesión; solo 401 (y 403 en menú) envía al login
- [ ] 1.10 Prueba manual en dev: con backend detenido a mitad de venta, el POS muestra "Problema de conexión", conserva el carrito y al reintentar (backend arriba) no duplica
- [ ] 1.11 Deploy Fase 1 (push a `main` en fme-backend y fme-backoffice; la migración corre sola vía entrypoint)

## 2. Fase 2 – Modo offline

- [ ] 2.1 Agregar dependencia `idb`; crear `lib/offline/db.ts` con stores `catalogo`, `clientes`, `maestras`, `contexto`, `outbox`, `meta`
- [ ] 2.2 `lib/offline/conectividad.ts`: heartbeat a `/health` (15 s, timeout 3 s), hook `useConectividad()` con estados EN_LINEA / SIN_CONEXION / SINCRONIZANDO
- [ ] 2.3 `lib/offline/cache.ts`: precarga y refresco (al entrar online + cada 30 min) de catálogo del local, clientes, maestras y turno activo; `navigator.storage.persist()`
- [ ] 2.4 Refactor POS: leer catálogo/clientes/maestras desde caché (online refresca caché, offline solo lee)
- [ ] 2.5 `lib/offline/outbox.ts`: encolar venta (`client_uuid`, payload, `fecha_venta_cliente`, `turno_caja_id`, `numero_provisorio`, estado, intentos, error)
- [ ] 2.6 `lib/offline/sync.ts`: sincronizador FIFO secuencial con `navigator.locks`, backoff, manejo 401 (pausa) y 4xx (CON_ERROR)
- [ ] 2.7 Flujo de venta único: encolar → enviar si hay conexión → imprimir comprobante normal o provisorio
- [ ] 2.8 Restricciones offline en UI: ocultar canje de puntos, cheques, medios con crédito/plazo, crear cliente; agregar "Consumidor final"
- [ ] 2.9 Bloquear venta offline si no hay turno de caja cacheado
- [ ] 2.10 Banner de estado + contador de pendientes en el POS
- [ ] 2.11 Comprobante interno offline (`BoletaTermica` variante) con `numero_provisorio` y leyenda "Comprobante interno – pendiente de sincronizar"
- [ ] 2.11b Medios de pago offline: permitir efectivo y tarjeta (Transbank); deshabilitar cheque y crédito/plazo
- [ ] 2.12 Service worker: verificar que `/admin/pedidos/pos` carga en frío sin red; `CacheFirst` para imágenes de productos; no cachear `/api/*`
- [ ] 2.13 Bloquear logout con ventas pendientes

## 3. Fase 3 – Operación y conciliación

- [ ] 3.1 Backend: aceptar ventas OFFLINE con stock insuficiente (permitir negativo) y generar alerta
- [ ] 3.2 Backend: respetar precio del payload en ventas OFFLINE y marcar `diferencia_precio`
- [ ] 3.3 Backend: asociar venta a `turno_caja_id` recibido; si el turno está cerrado registrar como ajuste post-cierre + alerta
- [ ] 3.4 Frontend: pantalla "Ventas pendientes" (lista, estado, error, reintentar, ver comprobante)
- [ ] 3.5 Frontend: cierre de turno exige conexión y outbox vacío en el equipo
- [ ] 3.6 Reportes de ventas por fecha usan `COALESCE(fecha_venta_cliente, fecha_creacion)`
- [ ] 3.7 Purga de ventas `SINCRONIZADA` con más de 7 días en el outbox

## 4. Verificación

- [ ] 4.1 `openspec validate add-ventas-offline-backoffice`
- [ ] 4.2 Prueba manual: DevTools → Offline, recargar POS, vender 3 ventas, volver online, verificar 3 pedidos sin duplicados, inventario y caja correctos
- [ ] 4.3 Prueba "API colgada": detener backend con red activa → POS pasa a Sin conexión en < 10 s
- [ ] 4.4 Prueba de corte a mitad de envío (respuesta perdida) → reintento no duplica
- [ ] 4.5 Prueba de dos pestañas abiertas → cada venta se sincroniza una sola vez
- [ ] 4.6 Deploy por fases (push a `main`) y verificación en producción con un local piloto
