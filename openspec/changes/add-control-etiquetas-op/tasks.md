# Tasks

## 1. Backend

- [x] 1.1 Columnas `etiquetas_impresas_at`, `etiquetas_impresas_por_id` + relación en `OrdenProduccion`; migración Alembic; verificar `upgrade head` y `downgrade -1` en el contenedor
- [x] 1.2 Schema `OrdenProduccionRead` con `etiquetas_impresas_at` y `etiquetas_impresas_por`
- [x] 1.3 Endpoints POST (producción/admin, solo FINALIZADA) y DELETE (admin) `/produccion/ordenes/{id}/etiquetas-impresas`; verificar con curl (200, 400 no finalizada, 404 otro tenant) — _verificado 200/403/404; el caso 400 (OP no finalizada) no se probó: no hay OP abiertas en local_

## 2. Backoffice

- [x] 2.1 Tipos y funciones en `lib/api/produccion.ts`
- [x] 2.2 Modal de etiquetas: aviso si ya fueron impresas, botón "Marcar como impresas" y "Desmarcar" (admin)
- [x] 2.3 Lista de Producción: badge pendiente/impresas en OP finalizadas y filtro "Etiquetas" (Todas / Pendientes / Impresas)

## 3. Verificación

- [ ] 3.1 Prueba manual del usuario en local antes de push
