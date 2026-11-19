# Pasarelas de pago y checkout de la tienda (guía de operación)

> Change OpenSpec: [`add-pasarelas-pago`](../openspec/changes/add-pasarelas-pago/) (diseño, spec y tareas).
> Integración n8n: [`document-integracion-n8n`](../openspec/changes/document-integracion-n8n/) y [`n8n/README.md`](../n8n/README.md).
> Implementado el 2026-11-18. Arquitectura portada de EffiCheck (`D:/ProyectosAI/EffiCheck/backend/app/pasarelas`,
> probada en producción con Flow y Khipu).

## 1. Qué hay

| Pieza | Dónde |
|---|---|
| Contrato de proveedor + adaptadores | `services/pasarelas/` (`base.py`, `mercadopago.py`, `flow.py`, `khipu.py`, `simulada.py`, `cifrado.py`, `config.py`) |
| Núcleo (intención, confirmación idempotente, conciliación, auto-confirmación del pedido) | `services/pagos_online.py` |
| Endpoints públicos `/api/pagos/*` y admin `/api/admin/pasarelas/*` | `routers/pagos_online.py` |
| Validación y verificación del correo del checkout | `utils/email_check.py`, `services/verificacion_email.py`, `routers/pedidos.py` |
| Tablas | `pasarelas_pago`, `pagos_online`, `verificaciones_email` (migraciones `b7e2a9c4d1f3`, `c4f8e2d6b1a9`) |
| Landing | `fme-landing/app/checkout/` (`page.tsx`, `resultado/`, `simulada/`), `lib/api/pagos.ts`, `lib/api/pedidos.ts` |
| Backoffice | `/admin/configuracion/pasarelas` (Mantenedores → Pasarelas de pago), tarjeta "Por entregar" del dashboard, filtros de Pedidos |
| Tests | `tests/test_pasarelas.py` (adaptadores y cifrado, sin red): `docker exec fme-backend python -m pytest tests/test_pasarelas.py -q --noconftest` |

Proveedores: **Mercado Pago** (Checkout Pro: tarjetas y saldo MP), **Flow** (Webpay y otros), **Khipu**
(solo transferencia bancaria) y **Simulada** (solo desarrollo). Un proveedor nuevo = un adaptador nuevo en
`services/pasarelas/` registrado en `__init__.py`; nada más cambia.

## 2. Flujo de compra

1. **Correo:** el cliente ingresa su correo en el checkout.
   - **Validación** (`POST /api/pedidos/validar-email`): formato real, dominio que existe y recibe correo (DNS/MX) y sugerencia de typo (`gmial.com` → `gmail.com`).
   - **Verificación** (`POST /api/pedidos/verificacion-email/enviar` y `.../confirmar`): código de 6 dígitos por correo vía n8n. Si es correcto, se entrega un token firmado de 30 días, que la landing guarda en el navegador.
2. **Crear el pedido** (`POST /api/pedidos/`): **exige `email_token`** y devuelve `token_seguimiento`.
3. **Iniciar el pago** (`POST /api/pagos`) con `pedido_id`, `token_seguimiento` y `pasarela_id`. El **monto lo fija el backend** desde el pedido: **productos (`monto_total`) + `costo_delivery`** (ver §2.1). Se crea una intención en `pagos_online` (vence en 15 min) y el cliente es redirigido al proveedor.
4. **Retorno y aviso:** el proveedor devuelve al cliente a `/api/pagos/retorno/{proveedor}?tenant=N` y avisa a `/api/pagos/webhook/{proveedor}?tenant=N`. **Ambos solo identifican el pago: el resultado siempre se consulta al proveedor.**
5. **Pago aprobado y monto correcto:**
   - el pedido queda `es_pagado`, con medio MERCADOPAGO, FLOW, KHIPU o PAGO_ONLINE;
   - **se confirma solo** (`autoconfirmar_pedido`): local de despacho por defecto del tipo de pedido, descuento de inventario, puntos ganados y estado CONFIRMADO;
   - luego se envía el correo "pedido confirmado" (n8n).
6. **No se pudo auto-confirmar** (por ejemplo, sin stock en el local de despacho): el pedido queda pagado y PENDIENTE y los admins reciben una notificación *"Pedido X pagado: confirmar manualmente"*. Aparece en el dashboard como **"Pagados sin confirmar"**.
7. **Casos en revisión** (`EN_REVISION`, también notificados):
   - el monto confirmado difiere del de la intención;
   - el pedido ya estaba pagado (pago duplicado) o fue cancelado → revisar devolución.
8. **Conciliación:** hilo de fondo cada 2 min (`pg_try_advisory_lock`) para las intenciones INICIADO de más de 5 min y EXPIRADO de las últimas 24 h. Recupera pagos cuyo aviso no llegó.
9. **Pantalla de resultado** (`/checkout/resultado?pago=<id>`): consulta cada 3 s y pide al backend consultar al proveedor cada 15 s, durante 5 min.

## 2.1. Retiro o delivery por comuna (change `add-delivery-por-comuna`)

- En el checkout el cliente elige **Retiro en casa central** (se muestra la dirección de *Configuración de la landing → footer → dirección*; costo $0) o **Delivery** (dirección + comuna elegida de una lista).
- Las comunas y sus precios se cargan en el backoffice: **Mantenedores → Tarifas de delivery** (`/api/admin/tarifas-delivery`). Solo aparecen las activas. **Sin tarifas cargadas, la tienda ofrece solo Retiro.**
- **Dirección con Mapbox:** el checkout autocompleta la dirección (Mapbox, como la calculadora de despacho) y toma la comuna de la sugerencia. El backend la vuelve a verificar (`services/geocodificacion.py`): si cae en otra comuna, rechaza el pedido; si Mapbox no la encuentra (p. ej. parcelas), el cliente marca una casilla confirmando la comuna y el pedido queda con la nota interna **"Dirección NO verificada: revisar antes de despachar"**. Variables: `MAPBOX_ACCESS_TOKEN` (backend) y `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` (build de la landing, secret de GitHub). Sin token, todo cae en confirmación manual.
- Envío gratis: si la configuración de la landing tiene `monto_minimo_delivery_gratis` y los productos (con descuento de puntos) lo alcanzan, el delivery cuesta $0.
- El **backend recalcula** el costo desde la tabla al crear el pedido (`services/tarifas_delivery.py`); nunca usa un monto del navegador. Guarda `modalidad_entrega`, `comuna_entrega` y `costo_delivery`. `monto_total` sigue siendo solo productos; el total a pagar es `monto_total + costo_delivery` (igual que en Cobranza).
- Público: `GET /api/tienda/entrega` → `{retiro: {direccion}, tarifas: [{comuna, costo}], monto_minimo_gratis}`.

## 3. Configurar una pasarela (por tenant)

Backoffice → **Mantenedores → Pasarelas de pago** (requiere el módulo `tienda_online` y rol admin).
El **superadmin** configura la de cada tenant entrando a él: Superadmin → **Operar en tenant** → misma pantalla.

1. **Nueva pasarela:** proveedor, nombre visible (lo que ve el cliente), ambiente (**Integración** = pruebas, **Producción** = dinero real) y orden. La de menor orden aparece primero y marcada "Recomendado".
2. **Credenciales:** son de solo escritura (nunca se vuelven a mostrar). Se guardan cifradas con AES-256-GCM, atadas al tenant y a la pasarela.
3. **Probar conexión.**
4. **Activar.** En Producción solo se puede si la última prueba fue exitosa y es posterior al último cambio de credenciales.
5. **Pasar a producción:** crear otra pasarela del mismo proveedor en ambiente Producción, cargar las credenciales reales, probar, activar y desactivar la de Integración. No requiere despliegue.

Con el backend en producción (`ENTORNO` distinto de `desarrollo`), las pasarelas de Integración y la Simulada **no se ofrecen** aunque estén activas (salvo el modo demo, abajo).

### Modo demo (mostrar el pago a un cliente sin cuenta real)

1. En el VPS, agregar al `.env` una clave larga: `echo "PASARELAS_CLAVE_DEMO=$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')" >> .env` y `docker compose up -d --force-recreate backend`.
2. Tener activa una pasarela de **Integración** (por ejemplo Khipu con la API key de la cuenta de desarrollador).
3. Abrir `https://www.masasestacion.cl/?demo=<clave>`: la clave queda en la pestaña (`sessionStorage`) y el checkout muestra también las pasarelas de Integración. Sin la clave, los visitantes ven lo de siempre. La Simulada nunca aparece en producción.
4. **El pedido de la demo es real:** queda pagado, se auto-confirma y descuenta stock. Después de la demo, **cancelarlo** en el backoffice.
5. Al terminar, quitar `PASARELAS_CLAVE_DEMO` del `.env` y recrear el backend.

### Mercado Pago
- Credenciales: [mercadopago.cl/developers](https://www.mercadopago.cl/developers) → Tus integraciones → Credenciales → **Access token**.
- En Integración se usan las credenciales de un **usuario de prueba vendedor**, y se paga con un **usuario de prueba comprador**.
- **Cuidado:** las credenciales de producción usadas con tarjetas de prueba fallan con *"Unauthorized use of live credentials"*.
- Rechazos: en Checkout Pro el comprador puede reintentar dentro del mismo pago, así que un rechazo no cierra la intención. Se muestra el motivo y la intención vence sola si no se aprueba.

### Flow
- **API key** y **Secret key**.
- Sandbox (`sandbox.flow.cl`) y producción (`www.flow.cl`) son **cuentas distintas**. Una key de producción en el sandbox responde *"apiKey not found"*.
- Exige el correo del pagador. Monto mínimo: $350.
- Sandbox: tarjeta `4051885600446623`, CVV `123`; banco simulado con RUT `11111111-1` y clave `123`.

### Khipu (solo transferencia)
- Una **API key** (API v3). No hay sandbox aparte; se usa una **cuenta de cobro en modo desarrollador** ([khipu.com](https://khipu.com), guía: [docs.khipu.com/en/quick-start](https://docs.khipu.com/en/quick-start)):
  1. Perfil → **Opciones de desarrollador** → activar el modo desarrollador.
  2. **Cuentas de cobro** → **Crear cuenta en modo desarrollador** → banco **DemoBank**, cualquier RUT, clave `1234`. Elegir la **Cuenta Personal** (cuenta de depósito, no la línea ni las tarjetas), cualquier plan y aceptar el contrato de prueba.
  3. En la cuenta creada: **Opciones de la cuenta → Para integrar Khipu a tu sitio web → Nueva API Key**. Se muestra **una sola vez**.
- Para pagar en pruebas: DemoBank, cualquier RUT, clave `1234`. La transferencia queda "verificando" unos minutos.
- Producción: el tenant abre su propia cuenta de cobro real (como empresa: cuenta corriente y representante legal) → nueva pasarela en Producción.
- Masas Estación (desarrollo) tiene una cuenta de cobro de prueba: "Masas Estación (desarrollo)", ID 532.969.

## 4. Variables de entorno

| Variable | Producción | Desarrollo |
|---|---|---|
| `ENTORNO` | sin definir o `produccion` (valor seguro por defecto) | `desarrollo` (en `docker-compose.yml`): habilita la Simulada y las pasarelas de Integración |
| `PASARELAS_CLAVE_MAESTRA` | **obligatoria**: 32 bytes en base64 (`python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"`). Si falta, la API arranca igual, pero las pasarelas responden 503 | opcional (se deriva de `SECRET_KEY`) |
| `URL_API_PUBLICA` | `https://api.masasestacion.cl` si el proxy no envía `X-Forwarded-Proto` | — |
| `MAPBOX_ACCESS_TOKEN` | token público de Mapbox (el mismo de la calculadora del backoffice); sin él, las direcciones de delivery quedan "no verificadas" | igual (en `.env`) |
| `PASARELAS_CLAVE_DEMO` | opcional; vacía = sin modo demo. Solo durante una demo | opcional |
| `URL_PUBLICA_PAGOS` | vacía | URL https de un túnel (`cloudflared tunnel --url http://localhost:8000`) para recibir los avisos del proveedor en local; sin túnel, la conciliación registra el pago igual |
| `N8N_WEBHOOK_VERIFICACION_EMAIL` | opcional (por defecto `https://n8n.effi4tech.cl/webhook/verificacion-email`) | igual |

⚠️ Si se pierde o cambia `PASARELAS_CLAVE_MAESTRA`, las credenciales guardadas ya no se pueden descifrar y hay que volver a cargarlas.

## 5. Probar en local

- Puertos: API `8000` (contenedor `fme-backend`), backoffice `3001`, landing con `npm run dev -- -p 3002`.
- Abrir la landing como **`http://masasestacion.local:3002`**, no como `localhost`: el dominio identifica el tenant y el CORS de desarrollo acepta `*.local`. Requiere `masasestacion.local` en el archivo `hosts` (ver `fme-landing/hosts-local.txt`).
- **Pasarela Simulada:** crear en el backoffice una pasarela "Simulada" en Integración y activarla. El checkout lleva a `/checkout/simulada` con los botones Aprobar y Rechazar.
- **Código de verificación sin depender del correo:** en desarrollo el backend lo escribe en el log:
  `docker logs fme-backend 2>&1 | grep "Código de verificación" | tail -1`
- **Cambios de variables de entorno:** hay que recrear el contenedor (`docker compose up -d backend`).
- **API colgada tras editar el backend:** con el backoffice abierto, su conexión de notificaciones (SSE) deja la recarga de uvicorn esperando (*"Waiting for connections to close"*). Solución: `docker restart fme-backend`.

## 6. Operación diaria

- **Dashboard → Por entregar:**
  - Confirmados, En Preparación y En Ruta (cada número abre Pedidos filtrado);
  - **Pagados sin confirmar** (en ámbar si hay alguno), que abre `/admin/pedidos?estado=PENDIENTE&pagado=si`.
- **Pedidos:**
  - nuevos filtros **En Ruta** y **Pago** (pagados / por pagar);
  - el filtro inicial se puede pasar por la URL (`?estado=`, `?pagado=si|no`);
  - "Creado por" muestra **🛒 Tienda online** en los pedidos que hizo el cliente en la landing.
- **Pasarelas de pago → Pagos en línea recientes:** estado de cada intento. **EN_REVISION requiere acción manual** (posible devolución en el panel del proveedor).
- **Stock:** la auto-confirmación descuenta del **local de despacho por defecto del tipo de pedido** (Masas Estación, "Productos Regulares": Lampa). Si ese local no tiene stock, el pedido queda "pagado sin confirmar" y se confirma a mano eligiendo otro local. La landing todavía muestra el stock **sumado de todos los locales** (pendiente, tarea 4.5 del change).

## 7. Checklist de producción

- [ ] `PASARELAS_CLAVE_MAESTRA` en el `.env` del VPS (y `URL_API_PUBLICA` si corresponde). `ENTORNO` sin definir.
- [ ] Workflow n8n **"FME - Código de verificación de correo"** (`VxFbcw9rerVw1ByA`) **activo**. Sin él, la tienda **no puede crear pedidos**.
- [ ] **Rotar el access token de Mercado Pago** que estuvo escrito en `docker-compose.yml` (y en el historial de git). Ya se quitó del archivo y no se usa.
- [ ] Crear la pasarela de producción del tenant en el backoffice, probarla y activarla.
- [ ] Probar una compra real de monto bajo y verificar que el pedido queda pagado, confirmado y con el inventario descontado.

## 8. Cambios incompatibles y eliminaciones

- Se eliminaron `/api/payments/*` (el Payment Brick, en el que **el navegador decidía el monto**) y `/api/test/test_webhook/{pedido_id}` (**sin autenticación, marcaba cualquier pedido como pagado**).
- También se eliminaron `services/payment_service.py` y `fme-landing/components/MercadoPagoBrick.tsx`. La dependencia `@mercadopago/sdk-react` de la landing ya no se usa.
- `POST /api/pedidos/` exige `email_token` (correo verificado).
- [`MERCADOPAGO_INTEGRATION.md`](../MERCADOPAGO_INTEGRATION.md) quedó obsoleto (describe el flujo anterior).
