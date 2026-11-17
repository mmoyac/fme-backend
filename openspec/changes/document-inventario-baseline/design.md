## Context

Ver proposal.md (Why). Esta es documentación retroactiva verificada contra el código y, para Existencias / Transferencias / Historial, contra el stack local (2026-11-16).

## Mapa del módulo: cómo se complementan

El inventario descansa en **dos almacenes de stock** y **dos historiales**:

| Almacén | Tabla | Unidad | Lo escriben | Historial |
|---|---|---|---|---|
| Stock por local | `inventario` (producto × local) | unidades / kg / lt (`Numeric 10,3`) | Pedidos, Producción, Devoluciones, Merma, Transferencia directa, Solicitudes, Conteo | `movimientos_inventario` → pestaña **Historial** |
| Stock de cajas | `stock_cajas_proveedor` (producto × proveedor) | cajas (lotes de carne) | Recepción (enrolamiento), Pedidos de cajas, Preventa, ajuste manual | `movimientos_stock_cajas` → vista **Movimientos** de Stock de Cajas |

```
                    ┌──────────── Stock por local (inventario) ────────────┐
 Compras/Producción ─▶ entradas                                            │
 Pedidos/POS ───────▶ salidas (PEDIDO)                                     │
 Existencias ───────▶ consulta + MERMA ──┐                                 │
 Conteo ────────────▶ AJUSTE_CONTEO ─────┼──▶ movimientos_inventario ──▶ Historial
 Transferencias ────▶ TRANSFERENCIA ─────┤        (un solo libro de auditoría)
 Solicitudes ───────▶ TRANSFERENCIA ─────┘                                 │
                    └──────────────────────────────────────────────────────┘

 Recepción (lotes) ─▶ Stock de Cajas (producto × proveedor) ◀─ Pedidos de cajas / Preventa
                       └─▶ movimientos_stock_cajas (vista Movimientos)
```

Cómo se usan juntas:
- **Existencias** es la foto: muestra el stock y alerta (semáforo) qué falta → se repone con **Transferencias** (movimiento inmediato, decide quien tiene el stock) o **Solicitudes** (la tienda que necesita pide y la que tiene aprueba).
- **Conteo** corrige la foto contra la realidad física; **Merma** registra pérdidas conocidas sin esperar un conteo.
- **Historial** es el libro único que explica cada cambio de Existencias (quién, cuándo, por qué); Conteo enlaza sus ajustes con "Ver conteo #N".
- **Stock de Cajas** es un mundo paralelo para carnes con lotes: no suma a Existencias y tiene su propio historial.

## Goals / Non-Goals

**Goals:** documentar las 6 piezas (5 capabilities aquí + `inventario-conteo`) y su relación; registrar brechas para changes posteriores.

**Non-Goals:** no cambiar código; no documentar Recepción/enrolamiento salvo su efecto en cajas; no redocumentar Conteo.

## Decisions

- **Una capability por pieza** (`inventario-existencias`, `-transferencias`, `-historial`, `-stock-cajas`, `-solicitudes-transferencia`, más `-conteo`): cada mejora pedida apunta a una pieza concreta y se escribe como delta acotado.
- **La spec describe el comportamiento funcional actual**; los huecos de seguridad y las inconsistencias **no se elevan a requisito**: se listan abajo y se corrigen en changes propios que agregan o modifican requisitos.
- **Orden de archivo**: `add-conteo-inventario` → este change → changes de mejora (sus deltas MODIFIED requieren que estas specs existan).

## Risks / Trade-offs — brechas observadas y change que las aborda

**Seguridad (urgente) → `fix-seguridad-inventario`**
- Solicitudes: `POST /`, `GET /{id}` y `DELETE /{id}` **sin autenticación** (verificado: `GET /api/solicitudes-transferencia/{id}` responde sin token); ningún endpoint salvo el listado filtra por tenant; el listado toma el tenant del hostname; el cliente fija `tenant_id`, `usuario_solicitante_id` y `estado_id` al crear.
- Stock de Cajas: `PUT /ajustar`, `POST /actualizar-desde-enrolamiento` y `POST /reservar-para-pedido` no filtran por tenant.

**Transferencia directa y merma → `fix-inventario-movimientos-trazabilidad`**
- Transferencia registra `usuario="admin"` fijo (verificado); solicitudes registran el id como texto; ninguna llena `usuario_id`.
- Merma, transferencia y solicitudes solo aceptan enteros (verificado: 1,5 → 422) aunque el stock es decimal.
- Sin bloqueo de fila en transferencias/finalización (riesgo de carrera).
- Transferencia directa y solicitudes duplican la lógica de mover stock con reglas distintas.

**Solicitudes → `improve-solicitudes-transferencia`**
- El backend no valida stock suficiente (puede dejar negativo), ni origen ≠ destino, ni productos/locales del tenant.
- Los ajustes de recepción no generan movimiento (no aparecen en Historial) y descuadran si falta la fila de inventario del destino.
- Eliminar no tiene control de estado ni de rol y no revierte stock; la UI ofrece "Eliminar" a todos y calcula permisos sin el rol admin.
- Editar ítems los borra y recrea; no hay estado de cancelación/rechazo; los estados se toman de la tabla de enrolamiento.
- Congelamiento reportado por el cliente: la pantalla no renderiza imágenes; causas probables: PDF generado con html2canvas en el hilo principal, catálogo completo (1000 productos con `imagen_url`) cargado varias veces y una request de stock por ítem en cada tecla. Requiere reproducir.

**Historial → `improve-inventario-historial`**
- Tope de 100 sin paginación; sin filtro por fecha; filtro de tipo con 6 de ~13 tipos; sin exportación.

**Existencias → `improve-inventario-existencias`**
- Carga hasta 1000 productos incluidos inactivos y operacionales (arriendo, luz, HH); orden de locales no definido.

**Stock de Cajas → `fix-stock-cajas-consistencia`**
- Ajuste acepta negativos, no actualiza la fecha ni los totales; el contador puede quedar negativo en pedidos.
- `/lotes-disponibles` no excluye lotes reservados en preventa.
- Movimientos de lotes sin antes/después y siempre "+1"; preventa no registra movimiento al cancelar/quitar.
- Etiquetas del resumen engañosas; listados truncados (100/50) sin paginar; errores del backend no se muestran.
- Solo cuenta la categoría con nombre exacto "CARNES".

## Migration Plan

No aplica (documentación). Archivar después de `add-conteo-inventario` y antes de los changes de mejora.
