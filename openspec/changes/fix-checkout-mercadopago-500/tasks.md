## 1. Diagnóstico de la causa raíz

- [x] 1.1 Obtener el traceback real del 500 — reproducido en dev: dos excepciones no controladas en `crear_pedido_frontend`
- [x] 1.2 Credenciales MP verificadas: las usadas en dev (PK `e472ead8`) son de PRODUCCIÓN — el token generado da `live_mode: true`, por eso las tarjetas de test fallan con 401 "Unauthorized use of live credentials". Falta obtener credenciales de prueba genuinas (`live_mode: false`)
- [x] 1.3 Reproducir el error localmente y confirmar la línea exacta (pedidos.py: `Cliente(comuna=...)` y `db.query(TipoDocumento)`)
- [x] 1.4 Causa raíz documentada: (a) `comuna` no es columna de `Cliente` → TypeError al crear cliente nuevo; (b) `TipoDocumento` no importado → NameError

## 2. Fix backend del 500

- [x] 2.1 Corregir la causa raíz en `crear_pedido_frontend`: quitar `comuna` del constructor de `Cliente` (preservándola dentro de `direccion`) e importar `TipoDocumento`. Verificado en dev: ambos flujos → 201
- [ ] 2.2 Envolver `crear_pedido_frontend` para que errores inesperados se capturen con contexto (no caer al middleware como 500 genérico)
- [ ] 2.3 En `process_payment` / `create_preference`, propagar el motivo real de Mercado Pago (rechazo, token, dato faltante) en el `detail`, no `str(e)` opaco

## 3. Observabilidad y logging

- [ ] 3.1 Reemplazar los `print("----> DEBUG ...")` de `services/payment_service.py` por logging estructurado
- [ ] 3.2 Loguear errores del flujo de pago con contexto (`pedido_id` / `external_reference`, medio de pago)

## 4. Frontend (fme-landing — coordinado)

- [ ] 4.1 En `app/checkout/page.tsx`, mostrar el `detail` real del backend en lugar del `alert()` genérico
- [ ] 4.2 Manejar de forma diferenciada los estados de pago aprobado / rechazado / pendiente del Brick

## 5. Verificación

- [ ] 5.1 Probar en producción un pago real con Mercado Pago de extremo a extremo (pedido creado → pago aprobado → CONFIRMADO → notificación)
- [ ] 5.2 Verificar que un error de negocio (p. ej. producto sin precio) muestra un `detail` accionable al cliente, no "Error interno del servidor"
- [ ] 5.3 Confirmar que el flujo "pago coordinado" sigue funcionando sin regresión
