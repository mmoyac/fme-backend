# Despacho Specification

## Propósito

Gestiona el flujo completo de **entrega de pedidos al cliente**, desde que un pedido
confirmado es asignado a un despachador hasta que es entregado. El módulo se divide
en dos subsistemas complementarios:

1. **Sistema de Despachos (Picking Flow)**: Flujo interno de preparación con estados
   `ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO`. Maneja la
   asignación, el proceso de picking de productos (incluido escaneo de QR/barcode
   para cajas variables) y el seguimiento de entrega.

2. **Hojas de Ruta**: Agrupador operacional de pedidos para un chofer y vehículo.
   Una hoja de ruta puede contener múltiples pedidos. Maneja el cálculo y pago del
   cobro al chofer.

El backend expone los endpoints bajo:
- `/api/despachos` → Sistema de Despachos (picking flow)
- `/api/hojas-ruta` → Hojas de Ruta

El backoffice (`/admin/despacho`) es el cliente que consume ambos. Toda operación
requiere usuario autenticado y activo; los datos están aislados por `tenant_id`.

---

## Modelo de Datos

### Despacho
```
Despacho
├── id
├── pedido_id (FK → Pedido, nullable)
├── solicitud_id (FK → SolicitudTransferencia, nullable)
├── despachador_user_id (FK → User)
├── estado_despacho: ASIGNADO | EN_PICKING | LISTO_EMPAQUE | EN_RUTA | ENTREGADO
├── fecha_asignacion
├── fecha_inicio_picking
├── fecha_fin_picking
├── fecha_inicio_ruta
├── fecha_entrega
├── notas_despacho
├── ubicacion_actual
└── hora_estimada_entrega
```

### PickingItem
```
PickingItem
├── id
├── despacho_id (FK → Despacho)
├── item_pedido_id (FK → ItemPedido)
├── usuario_picking_id
├── cantidad_solicitada / cantidad_pickeada
├── lote_codigo, peso_solicitado, peso_real
├── fecha_vencimiento, ubicacion_picking
├── codigo_barras_escaneado
├── fecha_picking, notas_picking
└── completado: bool
```

### HojaRuta
```
HojaRuta
├── id
├── tenant_id
├── vehiculo_id (FK → Vehiculo)
├── chofer_id (FK → User)
├── estado: PENDIENTE | EN_RUTA | COMPLETADA
├── fecha_salida, fecha_retorno
├── tipo_cobro_chofer: FIJO | POR_KG
├── tarifa_chofer
├── monto_cobro_chofer (calculado)
├── cobro_chofer_pagado: bool
├── notas
└── items: HojaRutaItem[]
    ├── pedido_id
    ├── entregado: bool
    ├── fecha_entrega
    └── notas_entrega
```

---

## Configuración de Delivery (`configuracion_landing`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `costo_fijo_delivery` | `Numeric(10,2)` | Costo base fijo por pedido |
| `costo_por_km_delivery` | `Numeric(10,2)` | Costo adicional por kilómetro |
| `costo_por_kilo_delivery` | `Numeric(10,2)` | Costo adicional por kilogramo (**agregado 2026-07-29**) |
| `monto_minimo_delivery_gratis` | `Numeric(10,2)` | Monto mínimo para delivery gratuito |
| `max_km_delivery` | `Numeric(6,2)` | Distancia máxima aceptada |

Existen en el response de `GET /api/config/landing` bajo la clave `delivery`:
```json
{
  "delivery": {
    "costo_fijo": 2000,
    "costo_por_km": 300,
    "costo_por_kilo": 20,
    "monto_minimo_gratis": 100000,
    "max_km": 14.5
  }
}
```
Migración aplicada: `c4d5e6f7a8b9_add_costo_por_kilo_delivery`

---

## Flujo del Sistema de Despachos (Picking Flow)

```
Pedido CONFIRMADO
       ↓
   ASIGNADO  ← POST /api/despachos/asignar/{pedido_id}
              ← POST /api/despachos/asignar-solicitud/{solicitud_id}
       ↓
  EN_PICKING  ← POST /api/despachos/{id}/iniciar-picking
       ↓      (crea PickingItems automáticamente)
  LISTO_EMPAQUE ← POST /api/despachos/{id}/completar-picking
       ↓        (todos los items deben estar completados)
    EN_RUTA   ← POST /api/despachos/{id}/iniciar-ruta
       ↓
  ENTREGADO   ← POST /api/despachos/{id}/confirmar-entrega
```

---

## Flujo de Hojas de Ruta

```
Pedidos CONFIRMADOS disponibles
       ↓
  Crear HojaRuta ← POST /api/hojas-ruta/
  (seleccionar pedidos, vehículo, chofer, tarifa)
       ↓
  Estado: PENDIENTE
       ↓
  Confirmar salida ← POST /api/hojas-ruta/{id}/salir
  (→ actualiza pedidos a EN_RUTA, registra fecha_salida)
       ↓
  Estado: EN_RUTA
       ↓
  Registrar entrega por ítem ← POST /api/hojas-ruta/{id}/items/{item_id}/entregar
  (→ actualiza pedido a ENTREGADO, dispara webhook email)
       ↓
  Calcular cobro chofer ← POST /api/hojas-ruta/{id}/calcular-cobro-chofer
  Marcar como COMPLETADA (manual via PUT)
       ↓
  Pagar chofer ← POST /api/hojas-ruta/{id}/pagar-chofer
  (→ cobro_chofer_pagado = true → desaparece de app despachador)
```

---

## Endpoints Implementados

### Sistema de Despachos (`/api/despachos`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/pendientes` | Lista unificada de pedidos confirmados y solicitudes con delivery pendientes de asignación |
| POST | `/asignar/{pedido_id}` | Asigna despacho a un pedido confirmado |
| POST | `/asignar-solicitud/{solicitud_id}` | Asigna despacho a una solicitud con `requiere_delivery=True` |
| GET | `/` | Lista despachos con filtros (estado, despachador, fechas) |
| GET | `/{despacho_id}` | Detalle de despacho con PickingItems |
| PUT | `/{despacho_id}` | Actualiza estado, hora estimada, notas |
| POST | `/{despacho_id}/iniciar-picking` | ASIGNADO → EN_PICKING, crea PickingItems |
| PUT | `/picking-item/{picking_item_id}` | Actualiza cantidad pickeada de un item |
| POST | `/{despacho_id}/completar-picking` | EN_PICKING → LISTO_EMPAQUE (requiere todos los items completos) |
| POST | `/{despacho_id}/iniciar-ruta` | LISTO_EMPAQUE → EN_RUTA |
| PUT | `/{despacho_id}/ubicacion` | Actualiza ubicación GPS actual |
| POST | `/{despacho_id}/confirmar-entrega` | EN_RUTA → ENTREGADO |
| POST | `/escanear-qr` | Escanea código de barras/QR de caja para picking |
| GET | `/resumen` | Métricas/estadísticas de despachos |

### Hojas de Ruta (`/api/hojas-ruta`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/pedidos-disponibles` | Pedidos con delivery (costo_delivery IS NOT NULL) confirmados sin asignar a hoja |
| POST | `/` | Crear hoja de ruta con pedidos, vehículo y chofer |
| GET | `/` | Listar hojas de ruta (filtros por estado, local) |
| GET | `/mis-hojas` | Hojas asignadas al chofer autenticado (app despachador) |
| GET | `/{hoja_id}` | Detalle completo con items y timeline |
| PUT | `/{hoja_id}` | Actualizar estado, notas, fecha_retorno |
| POST | `/{hoja_id}/salir` | Confirmar salida → EN_RUTA, actualiza pedidos |
| POST | `/{hoja_id}/items/{item_id}/entregar` | Marcar ítem entregado → pedido ENTREGADO |
| POST | `/{hoja_id}/calcular-cobro-chofer` | Calcula monto a pagar al chofer |
| POST | `/{hoja_id}/pagar-chofer` | Registra pago al chofer |
| POST | `/pagar-masivo` | Paga múltiples hojas de un chofer a la vez |
| DELETE | `/{hoja_id}` | Eliminar hoja (solo estado PENDIENTE) |

---

## Páginas del Backoffice (`/admin/despacho`)

### `/admin/despacho` — Índice
Página de bienvenida con cards de navegación a los subsistemas:
- Hojas de Ruta
- Picking de Cajas
- Vehículos (`/admin/vehiculos`)
- Tablero (`/admin/despacho/tablero`)
- Calculadora
- Resumen de Cajas

### `/admin/despacho/rutas` — Hojas de Ruta
**Estado: ✅ Implementado**

Vista principal de gestión de hojas de ruta:
- Lista de hojas activas con barra de capacidad kg (verde/amarillo/rojo)
- Modal para crear nueva hoja:
  - Selector de vehículo y chofer
  - **"Cobro del chofer"** (FIJO | POR_KG) — al cambiar tipo se auto-rellena la tarifa con el valor de `configuracion_landing` (`costo_fijo_delivery` o `costo_por_kilo_delivery`)
  - Lista de pedidos disponibles con checkbox — **solo pedidos con `costo_delivery IS NOT NULL`** (pedidos que solicitaron delivery, incluyendo delivery gratis)
  - Cada pedido muestra badge de sucursal de origen (`local_nombre`)
  - **Panel de estimado en tiempo real** (visible al seleccionar al menos 1 pedido con tipo de cobro activo):
    - Costo fijo base: `costo_fijo_delivery` del tenant
    - Por kilo: `kg_seleccionados × costo_por_kilo_delivery`
    - Por km / delivery: suma de `costo_delivery` de los pedidos seleccionados (ya calculado en el pedido)
    - Pago al chofer: cálculo según tipo (FIJO o POR_KG × kg_seleccionados × tarifa)
- Botón "Marcar En Ruta" por hoja
- Acciones de pago masivo al chofer
- Navegación al detalle de cada hoja

### `/admin/despacho/rutas/[id]` — Detalle Hoja de Ruta
**Estado: ✅ Implementado**

- Información del vehículo y chofer
- Lista de ítems (pedidos) con botón "Marcar Entregado" + modal de notas
- Botón "Confirmar Salida" (visible solo si estado=PENDIENTE)
- Cálculo y pago de cobro al chofer
- Timeline de ruta con timestamps

### `/admin/despacho/tablero` — Tablero
**Estado: ✅ Implementado**

Dashboard operacional en tiempo real (refresco cada 60s):
- Resumen de hojas del día (PENDIENTES / EN_RUTA / COMPLETADAS)
- Lista de hojas activas con barra KG y botón "Salir"
- Lista de pedidos confirmados aún sin asignar a ruta
- Badges de estado + alertas de pago pendiente al chofer

### `/admin/despacho/calculadora` — Calculadora de Despacho
**Estado: ✅ Implementado**

Calcula costo y tiempo estimado de una entrega usando Mapbox:
- Autocompletado de dirección origen y destino (Geocoding v5, filtrado a Chile)
- Ruta de conducción via Mapbox Directions v5
- Tarifas leídas desde `configuracion_landing` del tenant via TenantContext (fallback: fijo=2000, km=150, kilo=0)
- Fórmula: `costo_total = costo_fijo + (km × costo_por_km) + (kg × costo_por_kilo)`
- Campo de peso total (kg) aparece solo si `costo_por_kilo > 0`
- Muestra: distancia, tiempo estimado, desglose de costos por componente

### `/admin/despacho/picking-cajas` — Picking de Cajas
**Estado: ✅ Implementado**

Interface para escanear cajas físicas del frigorífico (QR/código de barras):
- Input de escaneo con foco automático
- Llama a `POST /api/preventa/escanear` para identificar la caja
- Si hay múltiples lotes candidatos, muestra selector
- Asigna la caja escaneada a un ítem de pedido (`asignarCajaAPedido`)
- Historial de escaneos de la sesión
- Acciones: desasignar caja

### `/admin/despacho/resumen-cajas` — Resumen de Cajas por Vendedor
**Estado: ✅ Implementado**

Vista de resumen por fecha:
- Selector de fecha
- Tabla expandible por vendedor → cortes → detalle de cajas
- Exportar PDF del frigorífico (`getFrigorificoPdfUrl`)
- Totales de peso y monto por vendedor

---

## Integraciones y Dependencias

### App del Despachador (`/despachador`)
- Usa `GET /api/hojas-ruta/mis-hojas` — hojas asignadas al chofer autenticado
- Solo muestra hojas con `cobro_chofer_pagado = false`
- Al hacer login con rol `despachador` redirige automáticamente a `/despachador`
- Control de acceso: rol `despachador` (case-insensitive) o `admin`

### Notificaciones Email (n8n)
- Al marcar ítem como entregado en hoja de ruta → webhook `pedido-entregado` → email al cliente
- Solo se envía si el canal de venta NO tiene `entrega_inmediata=True`

### Página de Seguimiento (pública)
- `GET /api/pedidos/seguimiento/{token}` — HTML con estado del pedido
- Si el pedido tiene delivery, muestra estado derivado de HojaRuta

### Módulo de Preventa (Cajas Variables)
- `POST /api/preventa/escanear` — identifica lote por QR/código de barras
- `POST /api/preventa/asignar-caja` — asigna lote escaneado a ítem de pedido
- `DELETE /api/preventa/desasignar-caja/{lote_id}` — desasigna lote

### Vehículos (`/api/vehiculos`)
- `GET /api/vehiculos/` — lista vehículos del tenant
- `GET /api/vehiculos/choferes` — lista usuarios con rol `despachador` **o `chofer`** (case-insensitive)
- Usado en Hojas de Ruta para asignar vehículo y chofer

---

## Reglas de Negocio Críticas

### Aislamiento por tenant
- Despachos se filtran por `Cliente.tenant_id` o `SolicitudTransferencia.tenant_id`
- Hojas de Ruta tienen campo `tenant_id` propio

### Transiciones de estado del Despacho
- Solo se puede iniciar picking desde estado `ASIGNADO`
- Solo se puede completar picking cuando **todos** los PickingItems tienen `completado=True`
- Las transiciones son unidireccionales (no hay rollback de estado)

### Transiciones de estado de la Hoja de Ruta
- Solo se puede eliminar una hoja en estado `PENDIENTE`
- Al confirmar salida (`POST /{id}/salir`): estado → EN_RUTA, actualiza pedidos a EN_RUTA, registra `fecha_salida`
- Al marcar ítem entregado: pedido → ENTREGADO, registra `fecha_entrega` en el ítem, dispara webhook email
- Al marcar como COMPLETADA (PUT): registra `fecha_retorno`

### Cobro del Chofer
- Dos modalidades: `FIJO` (tarifa por hoja) o `POR_KG` (tarifa × kg total entregado)
- Al seleccionar tipo de cobro en el formulario, la tarifa se **auto-rellena** desde `configuracion_landing`:
  - `FIJO` → usa `costo_fijo_delivery`
  - `POR_KG` → usa `costo_por_kilo_delivery`
- El usuario puede ajustar la tarifa manualmente antes de crear
- `cobro_chofer_pagado=True` hace desaparecer la hoja de la app del despachador
- El pago masivo (`POST /pagar-masivo`) paga varias hojas de un mismo chofer

### Pedidos elegibles para Hoja de Ruta
- Solo se muestran pedidos con `costo_delivery IS NOT NULL`
- `NULL` = venta POS/mostrador sin delivery → **excluido**
- `0` = delivery gratis (monto superó `monto_minimo_delivery_gratis`) → **incluido**
- `> 0` = delivery cobrado → **incluido**
- El `costo_delivery` del pedido ya refleja el costo calculado (fijo + km) al momento de la venta;
  se reutiliza en el panel de estimado sin necesidad de recalcular con Mapbox

### Picking de Cajas
- El escaneo puede retornar múltiples lotes candidatos (mostrar selector al usuario)
- Un lote asignado bloquea su reasignación hasta desasignar primero
- El historial de escaneos es solo de sesión (no persiste en BD)

---

## Estado Actual y Observaciones

### Lo que está funcionando
- ✅ Hojas de ruta completas (crear, salir, entregar, pagar chofer)
- ✅ Tablero con refresco automático
- ✅ App del despachador (`/despachador`)
- ✅ Picking de cajas con escáner QR
- ✅ Resumen de cajas por vendedor con PDF
- ✅ Calculadora de costos con Mapbox (tarifas desde config del tenant)
- ✅ Sistema de Despachos (picking flow) en backend: todos los endpoints implementados
- ✅ Filtro de pedidos con delivery (`costo_delivery IS NOT NULL`)
- ✅ Auto-relleno de tarifa del chofer desde config del tenant
- ✅ Panel de estimado en tiempo real al crear hoja de ruta
- ✅ `local_nombre` y `local_direccion` en pedidos disponibles
- ✅ `costo_por_kilo_delivery` en config del tenant (migración `c4d5e6f7a8b9`)

### Lo que está incompleto / pendiente
- ⚠️ El Sistema de Despachos (picking flow ASIGNADO→ENTREGADO) no tiene páginas
  propias en el backoffice. Los endpoints de `/api/despachos` existen en backend pero
  el frontend usa principalmente Hojas de Ruta como flujo operativo.
- ⚠️ El endpoint `GET /api/despachos/{despacho_id}` filtra solo por `Pedido→Cliente.tenant_id`,
  no contempla `solicitud_id` (puede retornar 404 para despachos de solicitudes).
- ⚠️ `GET /resumen` no valida acceso por tenant (no hay filtro explícito).
- ⚠️ La calculadora usa constantes hardcodeadas (2000 CLP fijo, 150 CLP/km) en lugar
  de leer `configuracion_landing.costo_fijo_delivery` / `costo_por_km_delivery`.
  → **RESUELTO 2026-07-29**: lee del TenantContext, agrega `costo_por_kilo_delivery`
- ⚠️ El tablero (`/admin/despacho/tablero`) duplica funcionalidad con `/admin/despacho/rutas`.
  Podría consolidarse.
