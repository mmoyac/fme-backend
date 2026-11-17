# Tasks

## 1. Servicio común

- [ ] 1.1 Crear `services/inventario_movimientos.py` con `transferir` y `registrar_merma` (tenant, validaciones, `FOR UPDATE` ordenado, usuario y `usuario_id`, decimales, `commit` opcional); verificar con tests de servicio contra PostgreSQL: transferencia válida, decimales, mismo local, stock insuficiente, otro tenant, merma válida/excesiva/decimal y dos transferencias concurrentes donde solo una se aplica

## 2. Endpoints

- [ ] 2.1 `POST /movimientos/transferencia` usa `transferir` con `cantidad` decimal; verificar por API que registra el usuario real y acepta 2.25
- [ ] 2.2 `POST /inventario/ajuste-merma` usa `registrar_merma` con `cantidad` decimal; verificar por API que acepta 0.75 y rechaza 0 y montos mayores al stock

## 3. Backoffice

- [ ] 3.1 `TransferenciasTab.tsx` y modal de merma en `ExistenciasTab.tsx`: inputs con `step="0.001"` y `parseFloat`; verificar en navegador una transferencia y una merma con decimales, y que Historial muestra el usuario real

## 4. Verificación

- [ ] 4.1 Ejecutar `openspec validate fix-inventario-movimientos-trazabilidad --strict` y verificar que pasa

## Actualizar capacitación

- [ ] Actualizar `capacitacion/inventario/06-historial-de-movimientos.html` si cambian los tipos, usuarios o notas de los movimientos (y `03-transferencias-directas.html` / `04-solicitudes-de-transferencia.html` si cambia lo que registran), con su fecha de "Última revisión"

## Workflow follow-up

- Archivar solo con OK del usuario, después de `add-conteo-inventario` y `document-inventario-baseline`.
