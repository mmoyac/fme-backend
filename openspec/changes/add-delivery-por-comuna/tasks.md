# Tasks

## 1. Modelo y migración

- [x] 1.1 Agregar modelo `TarifaDelivery` y columna `Pedido.comuna_entrega` en `database/models.py`; verificar que el backend arranca
- [x] 1.2 Crear migración Alembic (`tarifas_delivery` + `pedidos.comuna_entrega`) y aplicarla en el contenedor `fme-backend`; verificar `alembic upgrade head` y `downgrade -1`/`upgrade head` sin errores

## 2. Tarifas de delivery (backend)

- [x] 2.1 Servicio `services/tarifas_delivery.py` (normalizar comuna, `costo_delivery(...)` con envío gratis); verificar con tests unitarios en `tests/test_tarifas_delivery.py` (tarifa, gratis, sin tarifa, retiro)
- [x] 2.2 Router admin `/api/admin/tarifas-delivery` (CRUD, aislado por tenant, 409 en duplicado, 422 en costo inválido) y público `GET /api/tienda/entrega`; registrar en `main.py`; verificar con curl contra la API local
- [x] 2.3 `crear_pedido_frontend`: exigir `modalidad_entrega`, recalcular `costo_delivery`, guardar `comuna_entrega`; actualizar `PedidoCreateFrontend`; verificar creando pedidos RETIRO y DESPACHO en local y revisando la fila en la BD

## 3. Pago en línea y modo demo (backend)

- [x] 3.1 `crear_intencion`: monto = productos + delivery; verificar con un pedido con delivery que la intención en `pagos_online` tiene el monto total
- [x] 3.2 `PASARELAS_CLAVE_DEMO` en `services/pasarelas/config.py`; `puede_cobrar`/`pasarelas_disponibles`/`crear_intencion` aceptan `demo`; `GET /api/pagos/opciones?demo=` y `POST /api/pagos` con `demo`; verificar con tests en `tests/test_pasarelas.py` (con clave, sin clave, clave incorrecta, Simulada nunca en producción)
- [x] 3.3 Agregar `PASARELAS_CLAVE_DEMO` a `docker-compose.yml` y `docker-compose.prod.yml`; verificar con `docker compose config`
- [x] 3.4 Documentar delivery por comuna y modo demo en `docs/PASARELAS_PAGO.md` (variables, cómo hacer una demo, cancelar el pedido después); verificar que los pasos documentados funcionan en local

## 4. Backoffice

- [x] 4.1 Pantalla Mantenedores → Tarifas de delivery (listar, crear, editar, activar/desactivar, eliminar) con su entrada en el menú; verificar en `localhost:3001`
- [x] 4.2 Detalle/listado de pedido muestra comuna de entrega y costo de delivery; verificar con un pedido de la tienda creado en local
- [x] 4.3 Actualizar `fme-backoffice/AGENTS.md` (§ mantenedores / pasarelas) con la pantalla nueva; verificar la sección escrita

## 5. Landing

- [x] 5.1 `lib/api`: `obtenerOpcionesEntrega()`, `modalidad_entrega`/`comuna` en crear pedido, clave demo desde `?demo=` a `sessionStorage` y enviada en opciones e inicio de pago; verificar con `npm run build`
- [x] 5.2 Checkout: bloque Retiro/Delivery, select de comunas, línea Delivery y total en el resumen, textos según modalidad; verificar en `http://masasestacion.local:3002` ambos caminos
- [x] 5.3 Actualizar `fme-landing/AGENTS.md` §2.4 (checkout) con entrega y modo demo; verificar la sección escrita

- [x] 5.4 Confirmación de comuna: etiqueta "Dirección en <comuna>", casilla obligatoria en el checkout, `confirma_comuna` exigido por el backend con DESPACHO y registrado en `notas_admin`; verificar con `tsc` y creando un pedido sin y con confirmación

- [x] 5.5 Autocompletar con Mapbox (`components/DireccionMapbox.tsx`), comuna desde la sugerencia, verificación en el backend (`services/geocodificacion.py`, `MAPBOX_ACCESS_TOKEN` en compose y `.env`), token en el build de la landing (`Dockerfile.prod`, workflow); verificar con tests de `test_tarifas_delivery.py` y pedidos de prueba (verificada, no encontrada sin y con casilla)

## 6. Verificación integrada (local)

- [ ] 6.1 Con `ENTORNO` sin definir (modo producción) y `PASARELAS_CLAVE_DEMO` definida en local: sin `?demo` no aparece Khipu de Integración; con `?demo=<clave>` aparece y se paga con DemoBank un pedido con delivery por productos + delivery; el pedido queda pagado y confirmado
- [ ] 6.2 Pedido "sin pagar ahora" con delivery: Cobranza muestra monto de cobro = productos + delivery

## Workflow follow-up

- Prueba del usuario en local antes de push a `main` (= producción).
- En el VPS: agregar `MAPBOX_ACCESS_TOKEN` al `.env` del backend; en GitHub (repo fme-landing) crear el secret `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN`; en Mapbox restringir el token a los dominios propios.
- En el VPS: agregar `PASARELAS_CLAVE_DEMO` al `.env` solo para la demo y quitarla después; cargar tarifas reales en el backoffice.
- Archivar después de `add-modalidad-entrega-pedido` y `add-pasarelas-pago`, con OK del usuario.
