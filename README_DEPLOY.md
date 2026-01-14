# 🚀 GUÍA RÁPIDA DE DEPLOY DESDE CERO

## 📋 RESUMEN EJECUTIVO

Este procedimiento te permite hacer deploy del ecommerce para un **nuevo cliente desde cero**, diferenciando entre datos específicos del negocio y configuración del sistema.

**¿Cuándo usar este procedimiento?**
- Vender el sistema a un nuevo cliente (ej: panadería → carnicería)
- Crear una nueva instancia limpia en producción
- Configurar un entorno de desarrollo para un cliente específico

## 🏗️ TIPOS DE TABLAS IDENTIFICADAS

### ✅ **TABLAS DE SISTEMA** (Se mantienen)
```sql
-- Configuración base del sistema
tipos_pedido, tipos_local, categorias_producto, tipos_producto
tipos_venta, tipos_proveedor, unidades_medida, medios_pago
roles, users (admin), menu_items, bancos
```

### ⚠️ **TABLAS DE NEGOCIO** (Se limpian/adaptan)
```sql  
-- Datos específicos del cliente
productos, locales, clientes, proveedores
inventario, precios, stock_cajas_proveedor, lotes
pedidos, items_pedido, turnos_caja, despachos
movimientos_*, puntos_cliente, recetas
```

## 🎯 TIPOS DE NEGOCIO SOPORTADOS

| Tipo | Descripción | Productos Ejemplo |
|------|-------------|-------------------|
| **panaderia** | Panadería/Repostería | Pan, tortas, empanadas, completos |
| **carniceria** | Carnicería/Frigorífico | Carnes, cecinas, aves |
| **lacteos** | Quesería/Lácteos | Quesos, leche, mantequilla, manjar |

## 🚀 DEPLOY AUTOMÁTICO (RECOMENDADO)

### Opción 1: Script Completo PowerShell
```powershell
# Navegar al directorio del backend
cd fme-backend

# Deploy completo (desarrollo)
.\scripts\deploy_completo.ps1 -TipoNegocio "panaderia" -NombreCliente "Panadería San Juan" -EmailAdmin "admin@panaderiasanjuan.cl"

# Deploy completo (producción)
.\scripts\deploy_completo.ps1 -TipoNegocio "carniceria" -NombreCliente "Carnicería Los Andes" -EmailAdmin "admin@carniceriaandes.cl" -Produccion
```

### Opción 2: Script Python Directo
```bash
# Validar sistema limpio
python scripts/validar_deploy_limpio.py --cliente "Nuevo Cliente"

# Deploy del cliente
python scripts/deploy_nuevo_cliente.py --tipo panaderia --nombre "Panadería San Juan" --email admin@panaderiasanjuan.cl --password admin123
```

## 📋 DEPLOY MANUAL (PASO A PASO)

### Paso 1: Validaciones Iniciales
```bash
# 1.1 Verificar entorno virtual
.\venv\Scripts\python.exe --version

# 1.2 Verificar conectividad API
curl http://localhost:8000/docs  # o https://api.masasestacion.cl/docs

# 1.3 Validar sistema limpio
python scripts/validar_deploy_limpio.py --cliente "Nuevo Cliente"
```

### Paso 2: Configurar Sistema Base (Una sola vez)
```bash
# 2.1 Tablas maestras
python scripts/seed_maestras_prod.py

# 2.2 Tipos de venta (UNITARIO, PESO_SUELTO, etc)
python scripts/seed_tipos_venta.py

# 2.3 Tipos de proveedor (CARNES, LACTEOS, etc)
python scripts/seed_tipos_proveedor.py

# 2.4 Tipos de documento (Factura, Boleta, etc)
python scripts/seed_tipos_documento.py

# 2.5 Roles y usuarios
python scripts/seed_roles_prod.py

# 2.6 Menú del backoffice
python scripts/seed_menu_rbac.py
```

### Paso 3: Deploy del Cliente Específico
```bash
# 3.1 Deploy automático
python scripts/deploy_nuevo_cliente.py \
  --tipo panaderia \
  --nombre "Panadería San Juan" \
  --email admin@panaderiasanjuan.cl \
  --password admin123
```

## 📊 ARCHIVOS DE TEMPLATE

Los CSVs están organizados por tipo de negocio:

```
docs/deploy_templates/
├── panaderia/
│   ├── productos_panaderia.csv    # Pan, tortas, empanadas
│   └── locales_panaderia.csv      # Panadería Central, Sucursal Plaza
├── carniceria/
│   ├── productos_carniceria.csv   # Carnes, cecinas, aves
│   └── locales_carniceria.csv     # Carnicería Principal, Frigorífico
└── lacteos/
    ├── productos_lacteos.csv      # Quesos, leche, mantequilla
    └── locales_lacteos.csv        # Quesería Principal, Planta
```

### Personalizar Templates
```bash
# Editar productos específicos
notepad docs/deploy_templates/panaderia/productos_panaderia.csv

# Formato CSV requerido:
# nombre,sku,descripcion,categoria_codigo,tipo_producto_codigo,precio_web,es_vendible_web,stock_minimo
```

## 🔐 CREDENCIALES Y ACCESO

### URLs de Acceso (Desarrollo)
- **API Docs:** http://localhost:8000/docs
- **Backoffice:** http://localhost:3001
- **Landing:** http://localhost:3000

### URLs de Acceso (Producción)
- **API Docs:** https://api.masasestacion.cl/docs
- **Backoffice:** https://admin.masasestacion.cl (puerto 3001)
- **Landing:** https://masasestacion.cl (puerto 3000)

### Credenciales Iniciales
- **Email:** admin@cliente.cl (personalizable)
- **Password:** admin123 (personalizable)

## 📄 REPORTES GENERADOS

Cada deploy genera automáticamente:

### Deploy Report
```
docs/deploy_reports/deploy_Panaderia_San_Juan_20260113_143022.md
```
- ✅ Resumen de datos cargados
- 📋 Archivos utilizados
- 🔐 Información de acceso
- 📝 Próximos pasos

### Validation Report
```
docs/validation_reports/validacion_Panaderia_San_Juan_20260113_142801.md
```
- 🔍 Estado del sistema antes del deploy
- ⚠️ Warnings sobre datos existentes
- ✅ Validaciones pasadas

## 🛠️ TROUBLESHOOTING

### Error: "Admin no se puede crear"
```bash
# Verificar si ya existe usuario admin
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin@fme.cl&password=admin"

# Si existe, el script usará ese usuario
# Si no existe, creará uno nuevo
```

### Error: "Categorías ya existen"
```bash
# Normal - el sistema detecta datos existentes y los reutiliza
# Ver logs para confirmar que no es un error real
```

### Error: "Productos duplicados"
```bash
# SKU debe ser único
# Editar CSV de productos para cambiar SKUs duplicados
notepad docs/deploy_templates/panaderia/productos_panaderia.csv
```

### Error: "No se puede conectar a API"
```bash
# Verificar que el backend esté corriendo
cd fme-backend
.\venv\Scripts\uvicorn.exe main:app --reload

# O con Docker
docker-compose up -d
```

## 📚 CASOS DE USO COMUNES

### Caso 1: Cliente Panadería Completa
```powershell
.\scripts\deploy_completo.ps1 \
  -TipoNegocio "panaderia" \
  -NombreCliente "Panadería Artesanal" \
  -EmailAdmin "admin@panaderiaartesanal.cl"
```

### Caso 2: Cliente Carnicería en Producción
```powershell
.\scripts\deploy_completo.ps1 \
  -TipoNegocio "carniceria" \
  -NombreCliente "Carnes Premium" \
  -EmailAdmin "gerencia@carnespremium.cl" \
  -Produccion
```

### Caso 3: Validar Antes de Deploy
```bash
python scripts/validar_deploy_limpio.py --cliente "Nuevo Cliente"
# Revisar reporte generado antes de proceder
```

## ⚠️ CONSIDERACIONES IMPORTANTES

### Seguridad
- **NUNCA** usar datos de un cliente en otro
- Cambiar contraseñas por defecto
- Validar que las tablas estén completamente limpias

### Configuración Post-Deploy
1. ✅ Configurar inventario inicial
2. 💰 Ajustar precios por local
3. 💳 Configurar MercadoPago
4. 🧪 Probar flujo completo de pedidos

### Backup y Rollback
```bash
# Backup antes del deploy
pg_dump fme_database > backup_pre_deploy.sql

# Rollback si es necesario
psql fme_database < backup_pre_deploy.sql
```

---

**✅ Deploy configurado correctamente**  
**📋 Documentación completa disponible en:** `docs/DEPLOY_DESDE_CERO.md`  
**🚀 Scripts listos para uso en:** `scripts/deploy_*.py`