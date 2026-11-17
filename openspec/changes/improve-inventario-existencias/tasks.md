# Tasks

## 1. Backend

- [ ] 1.1 Función de servicio que calcula existencias (activos con `afecta_inventario`, locales activos ordenados con WEB al final y consolidado, semáforo, filtros local/categoría/solo_alertas) y endpoint `GET /inventario/existencias`; verificar con tests de servicio: excluye operacional e inactivo, WEB = suma, semáforo, filtros, aislamiento por tenant
- [ ] 1.2 `GET /inventario/existencias/excel` con la misma función; verificar con test que abre el xlsx y coincide con el endpoint JSON para los mismos filtros

## 2. Backoffice

- [ ] 2.1 `ExistenciasTab.tsx` consume `/inventario/existencias`, agrega filtros de categoría y local y botón "Exportar Excel"; mantiene búsqueda, "Solo mostrar alertas" y merma; verificar en navegador (Aji salsa sigue mostrando WEB 40 y semáforo correcto; ARRIENDO no aparece)

## 3. Verificación

- [ ] 3.1 Ejecutar `openspec validate improve-inventario-existencias --strict` y verificar que pasa

## Actualizar capacitación

- [ ] Actualizar `capacitacion/inventario/01-existencias-y-alertas.html` (y `02-registrar-merma.html` si cambia el botón o el modal de merma) con los cambios de Existencias, y su fecha de "Última revisión"

## Workflow follow-up

- Archivar solo con OK del usuario, después de `document-inventario-baseline` y `fix-inventario-movimientos-trazabilidad`.
