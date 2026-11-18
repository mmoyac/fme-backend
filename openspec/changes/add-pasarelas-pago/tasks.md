## 1. Backend: modelo y cifrado
- [x] 1.1 Modelos `PasarelaPago` y `PagoOnline`; migración `b7e2a9c4d1f3` (tablas + medios FLOW, KHIPU, PAGO_ONLINE)
- [x] 1.2 `services/pasarelas/config.py` y `cifrado.py` (AES-256-GCM, clave obligatoria en producción)

## 2. Backend: contrato y adaptadores
- [x] 2.1 Portar `base.py`, `flow.py`, `khipu.py`, `simulada.py` de EffiCheck
- [x] 2.2 Adaptador `mercadopago.py` (Checkout Pro, verificación por `external_reference`)

## 3. Backend: flujo, endpoints y conciliación
- [x] 3.1 Núcleo `services/pagos_online.py` (intención, confirmación idempotente, revisión, conciliación)
- [x] 3.2 Router `routers/pagos_online.py` (público + admin) y registro en `main.py`; hilo de conciliación en startup
- [x] 3.3 `token_seguimiento` en la respuesta de `POST /api/pedidos/`
- [x] 3.4 Eliminar `/api/payments/*`, `/api/test/test_webhook` y `services/payment_service.py`

## 4. Frontends
- [x] 4.1 Landing: checkout con pasarelas, `/checkout/resultado`, `/checkout/simulada`; eliminar Payment Brick
- [x] 4.2 Backoffice: pantalla Pasarelas de pago + listado de pagos en línea

- [x] 4.3 Confirmación automática del pedido pagado (`autoconfirmar_pedido`) + notificaciones a admins (sin confirmar / en revisión)
- [x] 4.4 Dashboard: tarjeta "Por entregar" (`GET /api/dashboard/por-entregar`) con enlaces a Pedidos filtrado; filtro EN_RUTA y `?estado=` en Pedidos
- [x] 4.6 Correo del checkout: validación de formato + dominio (DNS) + sugerencia de typo (`utils/email_check.py`)
- [x] 4.7 Verificación del correo con código de 6 dígitos (`services/verificacion_email.py`, tabla `verificaciones_email`, migración `c4f8e2d6b1a9`); `POST /api/pedidos/` exige `email_token`
- [x] 4.8 Workflow n8n "FME - Código de verificación de correo" (ID `VxFbcw9rerVw1ByA`, webhook `verificacion-email`, SMTP de "Email Confirmación Compra") creado y activo 2026-11-18; respaldo en `n8n/workflows/` (exportado con `scripts/n8n_exportar.py`). Si se desactiva, la tienda no puede crear pedidos
- [x] 4.9 Pedidos: filtro `pagado` (API + selector "Pago"), `?pagado=` en la URL; "Pagados sin confirmar" del dashboard enlaza a `?estado=PENDIENTE&pagado=si`
- [x] 4.10 Pedidos: canal de venta en el listado; "Creado por" muestra 🛒 Tienda online en pedidos de la landing
- [ ] 4.11 Limpieza: quitar `NEXT_PUBLIC_MP_PUBLIC_KEY` (landing `.env*`, `Dockerfile.prod`, workflow `docker-publish.yml`) y la dependencia `@mercadopago/sdk-react`, ya sin uso
- [ ] 4.5 (Propuesto) Landing: mostrar stock del local de despacho por defecto, no la suma de todos los locales

## 5. Pruebas
- [x] 5.1 Tests unitarios de adaptadores y cifrado (`tests/test_pasarelas.py`, 18 OK)
- [x] 5.2 E2E local con la pasarela Simulada (crear, reutilizar, aprobar idempotente, bloquear doble pago, retorno, webhook desconocido)
- [x] 5.6 Khipu DemoBank en local (cuenta de cobro de desarrollo "Masas Estación (desarrollo)"): pagos 00129 y 00130 confirmados por el proveedor; auto-confirmación OK en 00129, y en 00130 por falta de stock en Lampa (alerta OK)
- [x] 5.7 Correo: validar-email (casos de formato, dominio, typo), código (envío, reenvío 429, incorrecto, correcto, reuso), pedido sin token o con token ajeno → 400, con token → 201; envío real vía n8n con ejecución success
- [ ] 5.3 Prueba manual con Mercado Pago de prueba (usuario de prueba vendedor + comprador) vía túnel https (`URL_PUBLICA_PAGOS`)
- [ ] 5.4 (Opcional) Flow sandbox
- [ ] 5.5 OK del usuario en local antes de subir a main

## 6. Producción
- [ ] 6.1 Definir `PASARELAS_CLAVE_MAESTRA` (y `URL_API_PUBLICA` si corresponde) en el `.env` del VPS; `ENTORNO` sin definir o `produccion`
- [x] 6.2a Quitar el access token de Mercado Pago de `docker-compose.yml` (2026-11-18)
- [ ] 6.2 Revocar/rotar en Mercado Pago ese access token (sigue en el historial de git)
- [ ] 6.4 Verificar que el workflow n8n `VxFbcw9rerVw1ByA` esté activo antes de desplegar (sin él la tienda no crea pedidos)
- [ ] 6.5 Seguir el checklist de `docs/PASARELAS_PAGO.md` §7
- [ ] 6.3 Crear la pasarela Mercado Pago PRODUCCION en el backoffice, probar y activar

## 7. Documentación
- [x] 7.0a Guía de operación `docs/PASARELAS_PAGO.md`; `MERCADOPAGO_INTEGRATION.md` marcado obsoleto; `AGENTS.md` (variables de entorno)
- [x] 7.0b `fme-landing/AGENTS.md` (checkout nuevo) y `fme-backoffice/AGENTS.md` (pantallas nuevas)

## 8. Actualizar capacitación
- [ ] 8.1 El módulo de ventas/tienda online no tiene lecciones en `capacitacion/`: crear lección "Pasarelas de pago" (configurar, pasar a producción, revisar pagos EN_REVISION) cuando se cree ese módulo de capacitación
