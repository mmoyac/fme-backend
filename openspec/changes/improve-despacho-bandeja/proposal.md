# Proposal

## Why

La portada de Despacho del backoffice (`/admin/despacho`) es solo un menú de tarjetas: no dice cuántos pedidos esperan despacho ni cuáles son. Los pendientes solo se ven dentro del modal "Nueva Hoja de Ruta" o en el Tablero, sin comuna ni filtros, así que armar una ruta por zona es manual. Además, un pedido pagado en línea que no se pudo confirmar solo (ej. MASAS-ESTACION-2026-00128, por falta de local de despacho por defecto) queda escondido en una alerta y nunca llega a Despacho. Con la comuna de entrega que ahora guarda la tienda (`add-delivery-por-comuna`) ya existe el dato para agrupar por zona.

## What Changes

- La portada `/admin/despacho` pasa a ser una **bandeja de trabajo**:
  - **Contadores** clicables: *Por despachar*, *Pagados sin confirmar*, *En ruta* y *Entregados hoy*.
  - **Lista de pendientes** (pedidos y solicitudes con delivery) con número, cliente o local, dirección, comuna, fecha, total y si está pagado.
  - **Agrupación por comuna** (chips con conteo, incluido "Sin comuna") y filtros por fecha y pagado/no pagado.
  - **Selección múltiple** y botón **"Crear hoja de ruta con seleccionados"**, que abre el flujo existente de Hojas de Ruta con esos pedidos ya marcados (con el control de capacidad del vehículo de siempre).
  - Las tarjetas actuales (Hojas de Ruta, Picking, Vehículos, Tablero, Calculadora, Resumen de Cajas) siguen accesibles.
- Backend: endpoint de **bandeja** aislado por tenant con contadores y pendientes, incluyendo la comuna de entrega.
- **Corrección de elegibilidad**: un pedido con `modalidad_entrega = RETIRO` no es despachable aunque tenga `costo_delivery = 0` (hoy la tienda guarda 0 en los retiros y la regla "costo no nulo" los haría aparecer como pendientes de despacho). Aplica también a `GET /api/hojas-ruta/pedidos-disponibles`.
- Fuera de alcance: mapa de entregas, coordenadas y optimización del orden de la ruta (change futuro).

## Capabilities

### New Capabilities

_(ninguna)_

### Modified Capabilities

- `despacho`: nueva bandeja de pendientes con contadores y filtros por comuna; regla de pedidos elegibles para hoja de ruta considera la modalidad de entrega; creación de hoja de ruta desde una selección.

## Impact

- **Backend**: `routers/hojas_ruta.py` (endpoint de bandeja y regla de elegibilidad compartida con `pedidos-disponibles`), schemas de respuesta. Sin migraciones: `pedidos.comuna_entrega`, `modalidad_entrega` y `es_pagado` ya existen.
- **Backoffice**: `app/admin/despacho/page.tsx` (bandeja), `app/admin/despacho/rutas/page.tsx` (abrir "Nueva Hoja de Ruta" con pedidos preseleccionados), cliente API de hojas de ruta.
- **Spec**: `openspec/specs/despacho/spec.md` (sección de la página índice y "Pedidos elegibles para Hoja de Ruta").
- **Capacitación**: no hay lecciones del módulo Despacho en `capacitacion/`; no hay lecciones afectadas.
