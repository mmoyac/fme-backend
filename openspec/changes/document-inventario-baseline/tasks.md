# Tasks

## 1. Verificar la spec contra el código

- [x] 1.1 Verificar Existencias en el backoffice local (semáforo, WEB consolidado, búsqueda, merma válida e inválida, aislamiento por tenant) contra `specs/inventario-existencias/spec.md` — verificado por navegador (Aji salsa: WEB 40 = 0+4+6+30, semáforo y merma deshabilitada en 0) y por API (merma 0/excesiva → 400, otro tenant → 404, válida descuenta y registra usuario)
- [x] 1.2 Verificar Transferencias contra `specs/inventario-transferencias/spec.md` — verificado por API (mismo local 400, stock insuficiente 400, 5 unidades Lampa→TilTil y reversa 201) y por código (resumen previo)
- [x] 1.3 Verificar Historial contra `specs/inventario-historial/spec.md` — verificado por API (filtros producto/local/tipo, merma con notas y usuario) y por navegador ("Ver conteo #N")
- [x] 1.4 Documentar Stock de Cajas y Solicitudes de transferencia desde el código (`specs/inventario-stock-cajas`, `specs/inventario-solicitudes-transferencia`) y verificar el hueco de autenticación de solicitudes (GET sin token → 404 en vez de 401)
- [x] 1.5 Agregar el mapa del módulo y las brechas agrupadas por change en `design.md`; verificar con `openspec validate document-inventario-baseline --strict`

## 2. Brechas

- [x] 2.1 Convertir todas las brechas en changes (decisión del usuario 2026-11-16: "todo"): `fix-seguridad-inventario`, `fix-inventario-movimientos-trazabilidad`, `improve-solicitudes-transferencia`, `improve-inventario-historial`, `improve-inventario-existencias`, `fix-stock-cajas-consistencia`

## Workflow follow-up

- Archivar solo con OK del usuario y **después** de `add-conteo-inventario`; antes de los changes de mejora.
