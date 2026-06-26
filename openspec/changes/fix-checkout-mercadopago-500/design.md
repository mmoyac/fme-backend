## Context

El checkout de `masasestacion.cl` ofrece dos vías de pago: "pago coordinado" (sin pasarela) y Mercado Pago. El flujo coordinado funciona; Mercado Pago falla con **"Error interno del servidor"**.

Trazado del flujo actual:

1. `app/checkout/page.tsx` → `crearPedido()` hace `POST /api/pedidos/`. Si el método es Mercado Pago, envía `medio_pago_codigo = "MERCADOPAGO"`; si es coordinado, no envía medio de pago.
2. Con pedido creado, se renderiza `MercadoPagoBrick`, que al pagar llama `processPayment()` → `POST /api/payments/process_payment`.
3. Ambos endpoints viven en `fme-backend`. `crear_pedido_frontend` (`routers/pedidos.py`) **no tiene try/except global**: cualquier excepción inesperada se propaga al middleware CORS de `main.py`, que la captura, loguea el traceback y devuelve `{"detail": "Error interno del servidor"}`.
4. El frontend muestra `alert(error.message)` con ese `detail`, de ahí el mensaje que ve el cliente.

Hallazgos de la investigación:
- "Error interno del servidor" es el fallback genérico del middleware para excepciones **no controladas** (no `HTTPException`). Por tanto la falla está en un punto sin manejo: el candidato principal es `crear_pedido_frontend`, aunque también podría originarse al serializar la respuesta o en `process_payment`.
- El medio de pago `MERCADOPAGO` **sí existe** en el seed (`scripts/seed_maestras.py`), así que la búsqueda de medio de pago no es la causa (esa rama además devuelve 400 controlado).
- La causa raíz exacta requiere **leer el traceback** que el middleware ya registra en los logs del servidor. No es accesible desde el entorno de desarrollo local actual.

## Goals / Non-Goals

**Goals:**
- Que un pedido con Mercado Pago se cree y procese sin 500.
- Que cualquier error del flujo de checkout llegue al cliente con un `detail` accionable, y al equipo con un log trazable.
- Cerrar la brecha de observabilidad que hoy oculta la causa real.

**Non-Goals:**
- Rediseñar el checkout o el modelo de pagos.
- Cambiar la pasarela de pago o agregar nuevos medios de pago.
- Cambios de esquema de base de datos.

## Decisions

### 1. Primero diagnosticar con el traceback real, antes de "parchear"
El middleware ya loguea `traceback.format_exc()`. La primera tarea es obtener ese traceback (logs de producción / reproducción local con `MP_ACCESS_TOKEN`) para identificar la línea exacta. **Alternativa descartada**: adivinar y blindar a ciegas todo el endpoint — arriesga ocultar el síntoma sin corregir la causa.

### 2. Manejo de errores por capas, no un try/except que trague todo
- Errores de **negocio/validación** → `HTTPException` 4xx con `detail` claro (ya se hace para varios casos; completar los faltantes).
- Errores **inesperados** → capturar en el endpoint, loguear con contexto (`pedido_id`/`external_reference`, medio de pago) y devolver un 500 con `detail` que no pierda trazabilidad. **Alternativa descartada**: depender solo del middleware global, que no tiene contexto del pedido y produce un mensaje genérico inútil para el cliente.

### 3. Propagar el error real de Mercado Pago
En `process_payment`/`create_preference`, cuando el SDK de MP devuelve un estado no-2xx o lanza, exponer el motivo (rechazo, token inválido, dato faltante) en el `detail`, en vez de `str(e)` opaco o 500 genérico. El `payment_service` ya tiene logs de debug temporales (`print("----> DEBUG MP RESPONSE")`) que deben convertirse en logging estructurado.

### 4. El frontend deja de enmascarar el error
`app/checkout/page.tsx` reemplaza los `alert()` genéricos por UI que muestra el `detail` del backend y diferencia estados de pago (aprobado/rechazado/pendiente). Tarea coordinada en `fme-landing` (repo distinto), referenciada aquí para completar el flujo de cara al cliente.

## Risks / Trade-offs

- **La causa raíz podría ser de configuración de entorno** (p. ej. `MP_ACCESS_TOKEN` ausente/erróneo en producción) y no de código → Mitigación: la tarea de diagnóstico verifica explícitamente la configuración de MP antes de tocar código.
- **Mostrar `detail` crudo al cliente puede filtrar mensajes técnicos** → Mitigación: para errores inesperados se muestra un mensaje amigable + referencia/log id; el `detail` específico se reserva para errores de negocio (4xx).
- **Cambio cross-repo** (backend + landing) → Mitigación: el fix del 500 (backend) es independiente y desplegable solo; la mejora de UI del landing es incremental y no bloquea.

## Migration Plan

1. Diagnóstico (lectura de logs / reproducción) → identificar causa raíz.
2. Fix backend + logging estructurado → desplegar a `main` (GitHub Actions → VPS).
3. Verificar en producción un pago de prueba con Mercado Pago.
4. Mejora de UI de errores en `fme-landing` → desplegar.

Rollback: el cambio backend es aditivo (manejo de errores/logging); revertir el commit restaura el comportamiento previo sin migraciones.

## Open Questions

- ¿La causa raíz es código o configuración de `MP_ACCESS_TOKEN` en producción? (a resolver en la tarea de diagnóstico)
- ¿El error ocurre en `crear_pedido_frontend` o en `process_payment`? El traceback lo confirmará.
