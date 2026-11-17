# Tasks

## 1. Regla de alcance

- [x] 1.1 Crear `utils/alcance_local.py` (`local_de_alcance`, `exigir_local`); verificar con tests unitarios: superadmin, admin, sin local → total; vendedor con local → su local

## 2. Backend

- [x] 2.1 Merma: `exigir_local` sobre `local_id`; verificar con test que un vendedor recibe 403 en otro local y puede en el suyo
- [x] 2.2 Transferencia: `exigir_local` sobre el origen; verificar con test (403 desde otro local, OK hacia cualquier destino)
- [x] 2.3 Historial: forzar el local propio para usuarios de local; verificar con test que filtrar por otro local devuelve solo movimientos del propio
- [x] 2.4 Conteo: iniciar, listar, detalle, items, finalizar, cancelar y Excel respetan el alcance; verificar con tests (403 en conteo ajeno, lista filtrada)

## 3. Backoffice

- [x] 3.1 Calcular `alcanceTotal` desde el usuario autenticado y pasarlo a las pestañas; verificar con `tsc --noEmit`
- [x] 3.2 Existencias: selector de local para alcance total (solo si hay más de un local físico); usuario de local ve solo su local, sin WEB y sin merma ajena; verificar en navegador como admin y como vendedor
- [x] 3.3 Transferencias: origen fijo y sin stock de destino para usuario de local; verificar en navegador
- [x] 3.4 Conteo: local fijo en "Nuevo conteo" y lista filtrada; Historial: sin filtro de local para usuario de local; verificar en navegador
- [x] 3.5 Confirmar que el formulario de Solicitud sigue mostrando el stock del local origen para un vendedor; verificar en navegador

## 4. Verificación

- [x] 4.1 Listar usuarios no admin sin `local_defecto_id` en la BD local y verificar que el reporte queda para revisar antes del deploy
- [x] 4.2 Ejecutar `openspec validate add-inventario-alcance-por-local --strict` y verificar que pasa

## Workflow follow-up

- Archivar solo con OK del usuario, después de `add-conteo-inventario` y `document-inventario-baseline`.
