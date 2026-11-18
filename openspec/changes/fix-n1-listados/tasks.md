# Tasks

## 1. Diagnóstico

- [x] 1.1 Medir tiempos reales en producción (Playwright, usuario admin de solo lectura): abrir pantalla 1,1–2,6 s, Producción 6,5 s; piso por llamada a la API ~250 ms; `GET /api/productos/?limit=1000` entre 0,3 y 4,5 s
- [x] 1.2 Contar consultas SQL por endpoint (app en proceso con `httpx.ASGITransport` + `event.listens_for(engine, 'before_cursor_execute')`) para los ~30 endpoints que usa el backoffice

## 2. Correcciones (consultas medidas con los datos locales)

- [x] 2.1 Productos: 179 consultas / 497 ms → 2 / 27 ms. Respuesta idéntica (173 productos)
- [x] 2.2 Pedidos: 17 → 7 consultas con 14 pedidos; ya no crece por pedido. Respuesta idéntica salvo el orden de los ítems, ahora fijo por id (4 combinaciones de filtros comparadas)
- [x] 2.3 Cobranza: 14 → 8; ya no crece por cobro. Respuesta idéntica
- [x] 2.4 Clientes: 9 → 2; el GET ya no escribe en la BD. Respuesta idéntica
- [x] 2.5 Dashboard › estadísticas: 35 → 27 (las restantes son fijas: 7 son una por día de la semana). Respuesta idéntica

## 3. Verificación

- [x] 3.1 `tests/test_capacitacion.py` y `tests/test_alcance_local.py` siguen pasando (33/33)
- [ ] 3.2 Tras el deploy, volver a medir producción y comparar con 1.1

## 4. Pendiente (fuera de este change)

- Endpoint de resumen para el dashboard (hoy el backoffice descarga listas completas para contar) y agrupar las 7 consultas diarias en una.
- Paginación en backend de pedidos, productos e inventario.
