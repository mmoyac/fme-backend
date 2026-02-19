# 🚀 PLAN DE ONBOARDING - MASAS ESTACIÓN

## Flujo Completo: Cliente → Desarrollo → Producción

```
┌──────────────────────────────────────────────────────────────────┐
│  FASE 1: RECOLECCIÓN DE DATOS DEL CLIENTE                       │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ 📄 Productos (Excel/CSV)
   ├─ 📦 Inventario inicial
   ├─ 🏢 Proveedores
   ├─ 🏪 Sucursales/Locales
   ├─ 👥 Clientes existentes (opcional)
   └─ 🎨 Configuración landing (formulario/Excel)
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 2: VALIDACIÓN EN DESARROLLO                               │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ ✅ Validar formato de archivos
   ├─ ✅ Validar SKUs únicos
   ├─ ✅ Validar categorías existen
   ├─ ✅ Validar RUTs de proveedores
   └─ ✅ Validar precios > 0
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 3: IMPORTACIÓN EN DESARROLLO (localhost:8000)             │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ 1. Script: import_tenant_data_dev.ps1
   ├─ 2. Importar productos (AGREGAR, no borrar)
   ├─ 3. Importar locales (AGREGAR, no borrar WEB)
   ├─ 4. Importar proveedores
   ├─ 5. Importar inventario inicial
   ├─ 6. Importar clientes
   └─ 7. Configurar landing page (actualizar)
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 4: REVISIÓN Y PRUEBAS EN DESARROLLO                       │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ 🔍 Cliente revisa catálogo en localhost:3000
   ├─ 🔍 Verificar precios correctos
   ├─ 🔍 Verificar stock calculado
   ├─ 🔍 Probar flujo de pedido completo
   └─ ✅ Cliente aprueba datos
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 5: EXPORTACIÓN DESDE DESARROLLO                           │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ Script: export_tenant_data_dev.ps1
   ├─ Generar: productos_export.json
   ├─ Generar: locales_export.json
   ├─ Generar: proveedores_export.json
   ├─ Generar: inventario_export.json
   ├─ Generar: clientes_export.json
   └─ Generar: config_landing_export.json
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 6: IMPORTACIÓN INCREMENTAL EN PRODUCCIÓN                  │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ Script: import_tenant_data_prod.ps1
   ├─ Modo: INCREMENTAL (agregar nuevos, no borrar existentes)
   ├─ Skip: Registros con SKU/codigo duplicado
   ├─ Log: Registrar qué se agregó vs qué ya existía
   └─ Backup automático antes de importar
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  FASE 7: VERIFICACIÓN EN PRODUCCIÓN                             │
└──────────────────────────────────────────────────────────────────┘
   │
   ├─ ✅ Verificar productos visibles en www.masasestacion.cl
   ├─ ✅ Verificar precios correctos
   ├─ ✅ Verificar stock agregado correctamente
   ├─ ✅ Verificar catálogo completo en backoffice
   └─ ✅ Prueba de pedido end-to-end
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  ✅ ONBOARDING COMPLETADO                                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📜 Reglas de Negocio CRÍTICAS

### ❌ LO QUE **NUNCA** SE BORRA EN PRODUCCIÓN:

1. **Usuarios y roles del sistema** (admin, vendedores)
2. **Local WEB** (codigo='WEB') - Es sistema, no del cliente
3. **Menús RBAC** - Configuración del backoffice
4. **Pedidos históricos** - Auditoría
5. **Categorías del sistema** - Son generales
6. **Tabla de tenants** - Multi-tenant principal

### ✅ LO QUE SE PUEDE AGREGAR/ACTUALIZAR:

1. **Productos** - Agregar nuevos, actualizar existentes por SKU
2. **Locales físicos** - Agregar sucursales del cliente
3. **Proveedores** - Agregar nuevos, actualizar por RUT
4. **Inventario** - Sumar stock nuevo, no reemplazar
5. **Clientes** - Agregar nuevos, actualizar por email
6. **Configuración landing** - Actualizar datos del tenant

---

## 🛡️ Sistema de Backups

**Antes de importar en producción:**
```sql
-- Backup automático de tablas críticas
CREATE TABLE productos_backup_20260219 AS SELECT * FROM productos WHERE tenant_id=1;
CREATE TABLE inventario_backup_20260219 AS SELECT * FROM inventario WHERE producto_id IN (...);
CREATE TABLE locales_backup_20260219 AS SELECT * FROM locales WHERE tenant_id=1;
```

**Si algo sale mal:**
```bash
# Rollback disponible
ssh root@168.231.96.205 "docker exec masas_estacion_backend \
  psql -U fme -d fme_database -c 'RESTORE FROM BACKUP...'"
```

---

## 📝 Scripts a Crear

1. ✅ `import_csv_to_dev.ps1` - Importar CSVs del cliente a desarrollo
2. ✅ `export_tenant_data.ps1` - Exportar datos de desarrollo a JSON
3. ✅ `import_incremental_prod.ps1` - Importar a producción (modo seguro)
4. ✅ `verify_tenant_data.ps1` - Verificar integridad post-importación
5. ✅ `rollback_import.ps1` - Revertir importación si falla

---

## 🎯 Siguiente Paso

¿Quieres que cree:
1. Los **templates de CSV/Excel** para el cliente
2. Los **scripts de importación** para desarrollo
3. Los **scripts de exportación/sincronización** a producción
4. El **script de validación** de datos

¿Por cuál empezamos?
