## 1. Vista de detalle (solo lectura)

- [x] 1.1 Crear `app/admin/compras/[id]/detalle/page.tsx` en fme-backoffice
- [x] 1.2 Cargar la compra con `getCompra(id)` y los catálogos (productos, proveedores, locales, tipos documento) para resolver nombres
- [x] 1.3 Mostrar cabecera de solo lectura: proveedor, local, fecha, tipo y N° de documento, notas, estado (con badge de color)
- [x] 1.4 Mostrar tabla de detalle (producto, cantidad, precio unitario, subtotal) y monto total
- [x] 1.5 Agregar botón "Volver" a la lista; sin acciones de edición

## 2. Acceso desde la lista

- [x] 2.1 En `app/admin/compras/page.tsx`, agregar enlace "👁️ Ver" a `/admin/compras/{id}/detalle`
- [x] 2.2 Para compras RECIBIDAS, reemplazar el texto estático "Procesada" por el enlace "Ver"

## 3. Verificación en desarrollo

- [x] 3.1 Compilar el frontend sin errores (lint/build de la ruta nueva)
- [ ] 3.2 Verificar en dev: abrir el detalle de una compra RECIBIDA y confirmar que muestra cabecera + detalle correctos
- [ ] 3.3 Verificar que desde la lista el enlace "Ver" funciona para PENDIENTE y RECIBIDA
- [x] 3.4 Validar la change con `openspec validate ver-detalle-compra`

## 4. Despliegue (junto con fix-compras-overflow-monto)

- [ ] 4.1 Confirmar con el usuario que dev quedó validado
- [ ] 4.2 Push a `main` con ambos cambios (backend overflow + frontend detalle)
- [ ] 4.3 Verificar en producción: ver detalle de una compra recibida y crear una compra de monto alto
