## Context

`User` tiene `local_defecto_id`, `role` (por tenant) e `is_superadmin`. Solicitudes ya usa la regla "no admin con local → solo su local" (`routers/solicitudes_transferencia.py`). En Inventario no hay ninguna restricción por local. `GET /api/inventario/` la consumen además Pedidos, Producción, Productos, Cotizaciones y Alertas.

## Goals / Non-Goals

**Goals:** una regla única de alcance, aplicada en backend a escrituras (merma, transferencia, conteo) y a las lecturas propias del módulo (historial, conteos); UI coherente.

**Non-Goals:** restringir `GET /api/inventario/` (rompería otros módulos); permisos por menú (ya existen por rol); cambiar Solicitudes (ya cumple).

## Decisions

- **`utils/alcance_local.py`** con:
  - `local_de_alcance(user) -> Optional[int]`: `None` = alcance total (superadmin, rol admin o sin `local_defecto_id`); si no, el `local_defecto_id`.
  - `exigir_local(user, local_id)`: 403 "No tienes acceso a ese local" si el usuario tiene alcance de local y `local_id` es otro.
  - Misma definición de admin que `_es_admin` de solicitudes (rol "admin" o superadmin).
- **Escrituras**: merma (`local_id`), transferencia (`local_origen_id`), conteo (iniciar con `local_id`; operar sobre `conteo.local_id`).
- **Lecturas del módulo**: historial fuerza `local_id = local propio`; listado de conteos fuerza el local; detalle/Excel de un conteo ajeno → 403.
- **Existencias**: el front decide con `local_de_alcance` expuesto en `/api/auth/users/me` (ya trae `local_defecto_id`, `role` e `is_superadmin`); calcula en el cliente `alcanceTotal`. El stock de otros locales sigue llegando por `GET /api/inventario/` (no restringido) pero no se muestra; con `improve-inventario-existencias` el endpoint `/inventario/existencias` aplicará el alcance en el backend.
  - *Alternativa*: restringir `GET /api/inventario/` con un parámetro opcional — se deja para `improve-inventario-existencias`, que crea un endpoint propio.
- **Transferencias (UI)**: usuario de local → origen fijo; el stock del destino no se muestra (no es su local).
- **Usuarios sin local asignado** tienen alcance total, igual que en Solicitudes; se recomienda asignar local a todo usuario de tienda (pantalla Usuarios).

## Risks / Trade-offs

- [Un vendedor ve stock ajeno llamando a `GET /api/inventario/` directo] → aceptado: es lectura y la necesitan otros módulos; las escrituras sí quedan bloqueadas. Se cierra al migrar Existencias a `/inventario/existencias`.
- [Usuarios de tienda sin local asignado mantienen acceso total] → revisar asignaciones en Usuarios antes del deploy.
- [Rol "admin" se identifica por nombre] → igual que el resto del sistema hoy.

## Migration Plan

Sin migraciones. Antes del deploy: listar usuarios no admin sin `local_defecto_id` y asignarles local. Deploy backend y backoffice juntos.
