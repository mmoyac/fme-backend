# Design

Referencia: EffiCheck `Docs/prompt-pasarelas-pago.md` y change `pasarelas-pago-flow` (decisiones D73–D76). Aquí solo
se registran las diferencias con EffiCheck.

## 1. Qué se paga
EffiCheck paga boletas de un socio autenticado. FME paga **un pedido de la landing**, comprado sin sesión. La credencial
para iniciar el pago es el `token_seguimiento` del pedido (64 hex, devuelto al crearlo). El monto de la intención es
`round(pedido.monto_total)` (ya descontados los puntos; el delivery se cobra aparte). El navegador nunca envía montos.

## 2. Tenant en retorno y notificación
Las llamadas de la landing identifican el tenant por `X-Forwarded-Host`. El proveedor llama al API (`api.masasestacion.cl`)
sin ese dato, así que el backend arma sus propias URLs con `?tenant=<id>` (más `intencion=<uuid>` cuando el proveedor
no devuelve su token). Todo lookup filtra por tenant y por proveedor; esos parámetros solo identifican, nunca prueban.

## 3. Adaptador Mercado Pago (Checkout Pro)
- `crear`: `POST /checkout/preferences` con un ítem por el monto total CLP, `external_reference = orden_comercio`,
  `back_urls` → retorno con `intencion`, `expires` + `expiration_date_to` (vencimiento + 2 min), `X-Idempotency-Key`,
  y `notification_url`/`auto_return` solo si las URLs son https. Redirección GET a `init_point`.
- Verificación: `GET /v1/payments/search?external_reference=<orden>` (el token guardado es el id de preferencia, que
  no sirve para consultar pagos) → `verifica_por_intencion = True`: el núcleo usa `consultar` también en retorno/aviso.
- Mapeo: algún `approved` → APROBADO (monto `transaction_amount`); `pending/in_process/authorized/in_mediation` o
  `rejected/cancelled` → PENDIENTE (en Checkout Pro el comprador puede reintentar en la misma preferencia, así que un
  rechazo no es definitivo; el motivo se guarda para mostrarlo); solo devueltos → RECHAZADO. La intención vence sola.
- `probar`: `GET /users/me` (401/403 = credenciales).
- Se descarta el Payment Brick: exigiría que el backend cree el pago con datos de tarjeta tokenizados del navegador;
  Checkout Pro mantiene el contrato de redirección común a todos los proveedores.

## 4. Aplicar el pago al pedido
Aprobado con monto correcto → `pedido.es_pagado = true`, `medio_pago` según proveedor (MERCADOPAGO, FLOW, KHIPU,
PAGO_ONLINE). Tras el commit, **confirmación automática** (`autoconfirmar_pedido`, decisión del usuario 2026-11-18, para
evitar sobreventa): local de despacho = `tipo_pedido.local_despacho_default_id`, `descontar_inventario`, puntos
ganados y estado CONFIRMADO, igual que la confirmación manual de un pedido WEB. No vuelve a descontar puntos usados (la
landing ya los aplicó al crear el pedido) ni registra venta en caja. Si no se puede (sin local por defecto, stock
insuficiente en ese local), el pedido queda pagado y PENDIENTE y se notifica a los admins del tenant
(`pedido_pagado_sin_confirmar`). Luego `trigger_pedido_confirmado` (correo vía n8n). Una intención EN_REVISION también
notifica (`pago_en_revision`).
- Pedido ya pagado o cancelado → intención EN_REVISION (posible devolución manual).
- Aprobado tras el vencimiento con el pedido aún pagable → se aplica; la intención queda CONFIRMADO con nota.
- Una intención vigente por pedido: si se repite con la misma pasarela se reutiliza su URL; con otra, 400.

## 5. Sesiones y concurrencia
SQLAlchemy síncrono; endpoints `def` o `run_in_threadpool` (incidente 2026-11-11). Cada paso con el proveedor usa su
propia sesión (`SessionLocal`); nunca hay HTTP al proveedor con filas bloqueadas.
Conciliación: hilo daemon iniciado en `startup`, cada 120 s, protegido con `pg_try_advisory_lock` para que con varios
procesos corra uno solo.

## 6. Entorno y secretos
- `ENTORNO`: solo `desarrollo` habilita la Simulada y las pasarelas INTEGRACION al cobrar. Ausente = producción
  (valor seguro). `docker-compose.yml` local fija `ENTORNO: desarrollo`.
- `PASARELAS_CLAVE_MAESTRA` obligatoria en producción. A diferencia de EffiCheck, su ausencia **no** impide arrancar
  la API (FME es más que pagos): las operaciones de pasarelas responden 503 y el admin ve el error.
- Generar: `python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"`.

## 7. Correo del checkout (ampliación)
- **Validación** (`utils/email_check.py`): usa `email_validator` con `check_deliverability` (DNS, timeout 4 s).
  - Si el DNS falla, no bloquea.
  - La sugerencia de typo usa una lista de dominios comunes, typos conocidos (`gmail.cl`, `gmial.com`…) y distancia de Levenshtein ≤ 2 sin empate.
  - Hace falta porque dominios con typo como `gmial.com` **tienen MX**, así que la verificación DNS sola no los atrapa.
- **Verificación con código** (`services/verificacion_email.py`): se decidió así porque el comprador de la tienda es anónimo y solo así se prueba que el buzón existe y es suyo.
  - Se guarda el HMAC-SHA256 del código (derivado de `SECRET_KEY`).
  - El token es `base64(json{t,e,x}).hmac`, a propósito **no** es un JWT de sesión, para que no pueda usarse para autenticarse.
  - El envío es asíncrono vía n8n. En desarrollo el código va al log.
  - La landing guarda el token en `localStorage` por correo (30 días), así que un cliente recurrente no repite la verificación en ese dispositivo.

## 8. Dashboard y Pedidos (ampliación)
- `GET /api/dashboard/por-entregar` cuenta pedidos CONFIRMADO, EN_PREPARACION y EN_RUTA, más los PENDIENTE con `es_pagado`.
- `GET /api/pedidos/?pagado=` filtra por `es_pagado`.
- El listado incluye `canal_venta_codigo` y `canal_venta_nombre`, declarados en `PedidoConRelaciones` (si no, el `response_model` los descarta).
- Las notificaciones a admins (`notify_admins_tenant`) se guardan solo en BD, sin empujarlas por SSE, porque pueden originarse en el hilo de conciliación y la `asyncio.Queue` no es segura entre hilos.

## 9. Fuera de alcance
Webpay directo, devoluciones por API, rotación de clave maestra por comando, auditoría en tabla (se usa log sin
valores), auto-confirmación del pedido pagado.
