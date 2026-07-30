## 1. Verificar el patrón CRUD contra el código real

- [ ] 1.1 Confirmar el patrón listar/obtener/crear/actualizar/eliminar en `routers/maestras.py` (categorías, tipos, unidades, tipos-documento, medios-pago, estados-cheque)
- [ ] 1.2 Confirmar validación de unicidad de `codigo` en crear y actualizar
- [ ] 1.3 Confirmar guards de borrado por uso (ej. categoría con productos, canal con pedidos)
- [ ] 1.4 Confirmar registros de sistema protegidos en `routers/canales_venta.py` (POS, LANDING, WHATSAPP, TELEFONO)
- [ ] 1.5 Confirmar niveles de autorización (usuario activo en lecturas; `get_current_admin_user` en escrituras donde aplica)

## 2. Verificar alcance de datos por mantenedor

- [ ] 2.1 Clasificar cada mantenedor como global o por tenant (revisar `tenant_id` en el modelo y filtros en el router)
- [ ] 2.2 Documentar la clasificación resultante en la spec `mantenedores`

## 3. Consolidar el inventario

- [ ] 3.1 Contrastar el inventario de la spec con las opciones de `fme-backoffice/app/admin/mantenedores/page.tsx`
- [ ] 3.2 Mapear cada mantenedor a su router backend y su componente `*List.tsx`
- [ ] 3.3 Confirmar las 3 opciones que redirigen a páginas dedicadas (Config. Landing, Usuarios, Tenants)

## 4. Finalizar

- [ ] 4.1 Ajustar la spec ante cualquier discrepancia encontrada en 1–3
- [ ] 4.2 `openspec validate document-mantenedores-baseline`
- [ ] 4.3 Archivar el change (`/opsx:archive`) para fusionar el delta en `openspec/specs/mantenedores/spec.md`
