# Tasks

## 1. Solicitudes de transferencia

- [x] 1.1 Agregar `get_current_active_user` al router en `main.py` y a cada endpoint; verificar que sin token todos responden 401 (curl contra el contenedor local)
- [x] 1.2 Crear helper `_obtener_solicitud` filtrando por `current_user.tenant_id` y usarlo en GET/PUT/DELETE; cambiar el listado para usar el tenant del usuario; verificar con tests de servicio que una solicitud de otro tenant responde 404
- [x] 1.3 En crear: fijar `tenant_id`, `usuario_solicitante_id` y estado PENDIENTE desde el servidor; verificar con test que valores enviados por el cliente se ignoran
- [x] 1.4 Restringir DELETE a admin o solicitante (403 en otro caso); verificar con test
- [x] 1.5 Quitar del `SolicitudForm.tsx` el envío de `tenant_id`/`usuario_solicitante_id`/`estado_id`; verificar creando una solicitud desde el backoffice local

## 2. Stock de Cajas

- [x] 2.1 Validar tenant del producto en `PUT /ajustar`, `POST /actualizar-desde-enrolamiento` y `POST /reservar-para-pedido`; verificar con test que un producto de otro tenant responde 404 sin cambiar el contador

## 3. Verificación

- [x] 3.1 Buscar llamadas a `/api/solicitudes-transferencia` y `/api/stock-cajas` en workflows n8n y scripts del repo y verificar que envían token
- [x] 3.2 Ejecutar `openspec validate fix-seguridad-inventario --strict` y verificar que pasa

## Workflow follow-up

- Archivar solo con OK del usuario, después de `document-inventario-baseline`.
