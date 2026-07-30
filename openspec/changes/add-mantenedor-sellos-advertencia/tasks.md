## 1. Backend — CRUD del catálogo de sellos

- [ ] 1.1 Agregar schemas `SelloAdvertenciaCreate` y `SelloAdvertenciaUpdate` en `schemas/etiquetas.py`
- [ ] 1.2 `POST /etiquetas/sellos` — crear sello (validar `codigo` único → 400 si duplicado; rol admin)
- [ ] 1.3 `PUT /etiquetas/sellos/{sello_id}` — actualizar sello (parcial; bloquear cambio de `codigo` en sellos de sistema)
- [ ] 1.4 `DELETE /etiquetas/sellos/{sello_id}` — eliminar con guards: 400 si es sello de sistema, 400 si tiene filas en `producto_sellos`
- [ ] 1.5 Marcar/identificar los 6 sellos del seed como de sistema (campo `es_sistema` o lista de códigos protegidos)
- [ ] 1.6 Ajustar `GET /etiquetas/sellos` si el mantenedor necesita ver también inactivos (ej. query param `incluir_inactivos`)

## 2. Frontend — mantenedor embebido en el módulo

- [ ] 2.1 Agregar llamadas CRUD de sellos en `fme-backoffice/lib/api/etiquetas.ts`
- [ ] 2.2 Crear componente `app/admin/mantenedores/components/SellosList.tsx` (listar/crear/editar/eliminar/activar)
- [ ] 2.3 Agregar la opción "Sellos de Advertencia" a la grilla `opciones` en `mantenedores/page.tsx` e importar/renderizar `SellosList` (embebido, NO página dedicada)

## 3. Verificación

- [ ] 3.1 Probar crear/editar/deshabilitar un sello desde `/admin/mantenedores`
- [ ] 3.2 Verificar que un sello de sistema no se puede eliminar
- [ ] 3.3 Verificar que un sello asignado a un producto no se puede eliminar (400)
- [ ] 3.4 Verificar que un sello deshabilitado desaparece del selector de sellos del producto

## 4. Finalizar

- [ ] 4.1 `openspec validate add-mantenedor-sellos-advertencia`
- [ ] 4.2 Archivar el change (fusiona el requirement en `openspec/specs/mantenedores/spec.md`)
