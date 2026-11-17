## 1. Catálogo y modelo

- [x] 1.1 `utils/modulos.py`: `NUCLEO`, `MODULOS`, `REQUIERE`, `validar_modulos()`
- [x] 1.2 Modelo `TenantModulo` y columna `MenuItem.modulo` en `database/models.py`
- [x] 1.3 Migración Alembic: tabla `tenant_modulos` (PK compuesta + CHECK), `menu_items.modulo`, relleno por `href`, 12 módulos para cada tenant existente; `downgrade`

## 2. Bloqueo en backend

- [x] 2.1 Dependencia síncrona `require_modulo(codigo)` (tenant desde usuario, API Key o host) con 403 `modulo_no_contratado`
- [x] 2.2 Aplicar `require_modulo` en `main.py` a cada router según el mapeo del design
- [x] 2.3 Routers compartidos: marcar por endpoint los públicos de `pedidos`/`productos` con `tienda_online`

## 3. Menú y roles

- [x] 3.1 `/api/auth/menu` filtra por módulos contratados
- [x] 3.2 `PUT /api/admin/roles/{id}/menu` rechaza (422) ítems de módulos no contratados; `GET /menu_items` indica el módulo de cada ítem
- [x] 3.3 `/api/auth/users/me` incluye `modulos` del tenant

## 4. Consola de plataforma

- [x] 4.1 `GET /api/superadmin/modulos` (catálogo) y `GET/PUT /api/superadmin/tenants/{id}/modulos` con validación de dependencias
- [x] 4.2 Crear tenant acepta lista de módulos
- [x] 4.3 Backoffice: casillas de módulos por tenant en la consola, con dependencias marcadas automáticamente
- [ ] 4.4 Registrar cada cambio de módulos en la bitácora (depende de `harden-platform-admin` fase 2)

## 5. Frontends

- [x] 5.1 Backoffice: filtrar pestañas de Mantenedores por módulo y manejar 403 `modulo_no_contratado`
- [x] 5.2 Landing: página "tienda no disponible" ante 403 `modulo_no_contratado`

## 6. Verificación local

- [x] 6.1 Script de verificación: catálogo, dependencias (422), 403 por módulo, menú filtrado, asignación rechazada, recontratación restaura menú
- [ ] 6.2 Probar quitando cada módulo en local a un tenant de prueba y recorrer el backoffice
- [ ] 6.3 Probar checkout de la landing con y sin `tienda_online` y el workflow n8n de emails
