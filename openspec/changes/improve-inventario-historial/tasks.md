# Tasks

## 1. Backend

- [ ] 1.1 Extraer en `routers/movimientos_inventario.py` una función que construya la query filtrada (tenant, producto, local, tipo, desde/hasta en hora de Chile) y usarla en `GET /historial`; agregar `desde`/`hasta` y tope `limit ≤ 500`; verificar con tests de servicio (filtro de fechas inclusivo, tope de limit, aislamiento por tenant)
- [ ] 1.2 Agregar `GET /movimientos/tipos` (tipos distintos del tenant); verificar con test que no incluye tipos de otro tenant
- [ ] 1.3 Agregar `GET /movimientos/historial/excel` (mismos filtros, máx. 10.000 filas, aviso de truncado, fechas en hora de Chile); verificar con test que abre el xlsx y valida filas y filtros

## 2. Backoffice

- [ ] 2.1 Actualizar `lib/api/movimientos.ts` (skip/limit, desde/hasta, tipos, descarga Excel) y verificar con `tsc --noEmit`
- [ ] 2.2 En `HistorialTab.tsx`: filtros de fecha, filtro de tipo poblado desde `/movimientos/tipos` con etiquetas para todos los tipos conocidos, botón "Cargar más" (pide limit+1) y botón "Exportar Excel"; verificar en navegador con más de 100 movimientos

## 3. Verificación integral

- [ ] 3.1 Recorrer el historial en local combinando filtros, paginar y exportar; verificar que el Excel coincide con la pantalla
- [ ] 3.2 Ejecutar `openspec validate improve-inventario-historial --strict` y verificar que pasa

## Actualizar capacitación

- [ ] Actualizar `capacitacion/inventario/06-historial-de-movimientos.html` (tabla de tipos, filtros, límite de movimientos y ejercicio) y su fecha de "Última revisión"

## Workflow follow-up

- Archivar solo con OK del usuario, después de `add-conteo-inventario` y `document-inventario-baseline`.
