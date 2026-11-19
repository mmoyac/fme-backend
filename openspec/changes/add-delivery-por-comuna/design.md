# Design

## Context

- `configuracion_landing` ya tiene campos de delivery (`costo_fijo_delivery`, `costo_por_km_delivery`,
  `costo_por_kilo_delivery`, `monto_minimo_delivery_gratis`, `max_km_delivery`) que se exponen en
  `GET /api/configuracion/...` pero la landing no usa. Solo se reutiliza `monto_minimo_delivery_gratis`; el resto queda
  como está (fuera de alcance).
- `pedidos.costo_delivery` existe y es "cobro aparte, no suma al total": `monto_total` = productos. Cobranza ya calcula
  `monto_cobro = monto_total + costo_delivery`. Se mantiene esa convención.
- `crear_pedido_frontend` fija `modalidad_entrega="DESPACHO"` y concatena la comuna en `clientes.direccion`
  (texto libre). El pedido no guarda dirección ni comuna propias.
- `services/pagos_online.crear_intencion` cobra `round(pedido.monto_total)`.
- `puede_cobrar` / `pasarelas_disponibles` excluyen INTEGRACION y SIMULADA cuando `config.es_produccion()`.

## Goals / Non-Goals

**Goals:** tabla de tarifas por comuna mantenida en el backoffice; costo calculado en el backend; pago en línea por
productos + delivery; modo demo seguro y desactivado por defecto.

**Non-Goals:** cálculo por km o por peso (no hay geocodificación); horarios o fechas de retiro; varias sucursales de
retiro (la casa central es una sola, su dirección viene de la configuración de la landing); mostrar el delivery en el
correo de n8n; dirección de entrega estructurada por pedido (sigue en `clientes.direccion`).

## Decisions

1. **Tabla `tarifas_delivery`** (`id`, `tenant_id` FK, `comuna` String(100), `comuna_normalizada` String(100),
   `costo` Numeric(10,0), `activo` bool, timestamps; `UNIQUE(tenant_id, comuna_normalizada)`). La normalización
   (minúsculas, sin tildes, trim) evita duplicados "Colina"/"colina ". *Alternativa descartada:* tabla maestra de comunas
   de Chile + precio: más datos que mantener para un caso que hoy cubre unas pocas comunas.
2. **`pedidos.comuna_entrega`** String(100) nullable: snapshot del nombre de la comuna al crear el pedido (la tarifa
   puede cambiar o borrarse después). No FK.
3. **El backend recalcula** el costo: el navegador envía `modalidad_entrega` y `comuna`; el costo lo obtiene
   `services/tarifas_delivery.costo_delivery(db, tenant_id, modalidad, comuna, monto_productos)`. Cualquier
   `costo_delivery` del body se ignora. El envío gratis compara contra `monto_total` ya con descuento de puntos.
4. **Monto de la intención** = `round(monto_total + costo_delivery)`. La verificación de monto del proveedor ya compara
   contra `PagoOnline.monto`, así que no cambia.
5. **Endpoints:** admin `GET/POST/PUT/DELETE /api/admin/tarifas-delivery` (rol admin, módulo `tienda_online`, filtrado
   por tenant del usuario); público `GET /api/tienda/entrega` (tenant por dominio, igual que `/api/pagos/opciones`) →
   `{retiro: {direccion}, tarifas: [{comuna, costo}], monto_minimo_gratis}`.
6. **Modo demo:** variable `PASARELAS_CLAVE_DEMO` (vacía = desactivado). `GET /api/pagos/opciones?demo=…` y
   `POST /api/pagos` con campo `demo` la comparan con `hmac.compare_digest`. `puede_cobrar(p, demo=False)`: en
   producción con `demo=True` acepta INTEGRACION, nunca SIMULADA. La confirmación (retorno, webhook, conciliación) no
   filtra por ambiente, así que un pago demo se confirma igual que uno real. La landing guarda `?demo=` en
   `sessionStorage` (sobrevive a la navegación catálogo → checkout → resultado) y lo envía en esas dos llamadas.
   *Alternativa descartada:* lista de correos autorizados: requiere mantenedor y no sirve para mostrar en un PC ajeno.
7. **Pedido demo:** se auto-confirma y descuenta stock como uno real (la demo muestra el flujo completo). Se documenta
   cancelarlo después en el backoffice.
8. **Landing:** el bloque "Entrega" va antes de los datos de dirección; con Retiro se ocultan dirección y comuna; con
   Delivery la comuna es un `<select>` con las tarifas. El resumen del pedido suma la línea "Delivery". El texto
   informativo "Recibirás un número de pedido…" se ajusta según la modalidad.

9. **Verificación de la dirección con Mapbox** (ya usado por la calculadora de despacho del backoffice). La landing
   autocompleta con Mapbox geocoding v5 (`country=cl`, `types=address`, proximidad Lampa) y toma la comuna del contexto
   `place` de la sugerencia. El backend vuelve a geocodificar `"<dirección>, <comuna>"` (`services/geocodificacion.py`,
   `MAPBOX_ACCESS_TOKEN`) y solo confía en relevancia ≥ 0,9: si cae en otra comuna, rechaza; si no la encuentra
   (parcelas rurales, token ausente, error de red), exige la casilla de confirmación y deja la nota "NO verificada".
   *Alternativas descartadas:* Google Places (requiere otra API key con facturación); OpenStreetMap/Nominatim (calidad
   irregular en Chile y política de uso que no admite autocompletar).

## Risks / Trade-offs

- [Clave demo filtrada → cualquiera paga con DemoBank y se confirma un pedido sin dinero] → la clave es larga y
  aleatoria, se cambia o se borra del `.env` tras la demo; el pedido queda con medio KHIPU y la intención guarda la
  pasarela, así que se identifica en "Pagos en línea recientes".
- [Comuna mal escrita en la tarifa] → el cliente elige de una lista, no escribe; el admin corrige en el mantenedor.
- [Mapbox no conoce direcciones rurales de Lampa] → nunca bloquea por "no encontrada": cae en confirmación manual y
  nota interna para el despachador.
- [Token público de Mapbox visible en la landing] → restringirlo por URL en el panel de Mapbox a los dominios propios.
- [Pedidos "sin pagar ahora" con delivery] → `costo_delivery` queda guardado y Cobranza ya lo suma al cobro.
- [Cambio de tarifa entre ver el checkout y enviar] → se cobra la tarifa vigente al crear el pedido; la landing muestra
  el total que devuelve el backend en la confirmación.

## Migration Plan

1. Migración Alembic: crear `tarifas_delivery` y agregar `pedidos.comuna_entrega` (nullable; sin backfill).
2. Deploy del backend (push a `main`); la migración corre sola en el entrypoint. Sin tarifas cargadas, la landing ofrece
   solo Retiro.
3. Cargar tarifas en el backoffice. Opcional: `PASARELAS_CLAVE_DEMO` en el `.env` del VPS y `docker-compose.prod.yml`.
4. Rollback: revertir el deploy; las columnas nuevas son nullable y no rompen la versión anterior.
