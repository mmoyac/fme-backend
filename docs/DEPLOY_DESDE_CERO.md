# 📋 PROCEDIMIENTO DE DEPLOY DESDE CERO - IDENTIFICACIÓN DE DATOS DE NEGOCIO

## 🎯 CONTEXTO
Este documento identifica qué tablas contienen **datos específicos del negocio** versus **configuración del sistema**, para poder hacer deployments limpios cuando se vende el ecommerce a diferentes clientes.

## 🏗️ CLASIFICACIÓN DE TABLAS

### 1. 🔧 **TABLAS DE CONFIGURACIÓN DEL SISTEMA** 
*(Se mantienen iguales para todos los clientes - Solo se ejecutan una vez)*

#### 1.1 Tablas Maestras de Configuración
```sql
-- Estas tablas son estructura del sistema
tipos_pedido                    -- (PRODUCTOS, CAJAS_VARIABLES)
tipos_local                     -- (VENTA, FRIGORIFICO, WEB)
categorias_producto             -- (PANADERIA, LACTEOS, etc + puntos fidelidad)
tipos_producto                  -- (Materia Prima, Producto Elaborado, etc)
tipos_venta                     -- (UNITARIO, PESO_SUELTO, CAJA_VARIABLE)
tipos_proveedor                 -- (CARNES, LACTEOS, PANADERIA)
tipos_vehiculo                  -- (CAMION, FURGON, CAMIONETA)
tipos_documento_tributario      -- (Factura, Boleta, Guía)
estados_enrolamiento           -- (PENDIENTE, EN_PROCESO, FINALIZADO)
ubicaciones                    -- (P1-A-01, P1-B-02 - ubicaciones físicas)
unidades_medida               -- (KG, UN, LT con conversiones)
medios_pago                   -- (EFECTIVO, TARJETA, CHEQUE)
estados_cheque                -- (PENDIENTE, COBRADO, RECHAZADO)
bancos                        -- (Banco Chile, BCI, etc)
```

#### 1.2 Tablas de Sistema de Usuarios
```sql
-- Autenticación y permisos (se resetean por cliente)
roles                         -- (admin, vendedor, despachador, etc)
users                        -- (Se crea admin inicial por cliente)
menu_items                   -- (Estructura del menú del backoffice)
rol_menu_items              -- (Permisos por rol)
```

### 2. 🏪 **TABLAS DE DATOS DE NEGOCIO**
*(Se deben limpiar/adaptar para cada cliente nuevo)*

#### 2.1 Catálogos Base del Negocio
```sql
productos                     -- ⚠️ ESPECÍFICO DEL NEGOCIO
locales                      -- ⚠️ ESPECÍFICO DEL NEGOCIO  
clientes                     -- ⚠️ ESPECÍFICO DEL NEGOCIO
proveedores                  -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

#### 2.2 Configuración de Precios e Inventario
```sql
inventario                   -- ⚠️ ESPECÍFICO DEL NEGOCIO
precios                      -- ⚠️ ESPECÍFICO DEL NEGOCIO
precios_proveedor           -- ⚠️ ESPECÍFICO DEL NEGOCIO
stock_cajas_proveedor       -- ⚠️ ESPECÍFICO DEL NEGOCIO
lotes                       -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

#### 2.3 Transacciones del Negocio
```sql
pedidos                      -- ⚠️ ESPECÍFICO DEL NEGOCIO
items_pedido                -- ⚠️ ESPECÍFICO DEL NEGOCIO
cheques                     -- ⚠️ ESPECÍFICO DEL NEGOCIO
movimientos_inventario      -- ⚠️ ESPECÍFICO DEL NEGOCIO
movimientos_stock_cajas     -- ⚠️ ESPECÍFICO DEL NEGOCIO
puntos_cliente              -- ⚠️ ESPECÍFICO DEL NEGOCIO
movimientos_puntos          -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

#### 2.4 Sistema de Caja
```sql
turnos_caja                 -- ⚠️ ESPECÍFICO DEL NEGOCIO
operaciones_caja            -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

#### 2.5 Sistema de Despachos
```sql
despachos                   -- ⚠️ ESPECÍFICO DEL NEGOCIO
picking_items               -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

#### 2.6 Sistema de Compras/Producción
```sql
compras                     -- ⚠️ ESPECÍFICO DEL NEGOCIO
detalles_compra            -- ⚠️ ESPECÍFICO DEL NEGOCIO
recetas                    -- ⚠️ ESPECÍFICO DEL NEGOCIO
ingredientes_receta        -- ⚠️ ESPECÍFICO DEL NEGOCIO
enrolamientos             -- ⚠️ ESPECÍFICO DEL NEGOCIO
```

## 📝 PROCEDIMIENTO DE DEPLOY DESDE CERO

### Paso 1: Preparar Base de Datos Limpia
```bash
# 1. Crear nueva base de datos
createdb fme_nuevo_cliente

# 2. Aplicar todas las migraciones
alembic upgrade head
```

### Paso 2: Seed de Tablas de Sistema (Una sola vez)
```bash
# Ejecutar scripts de configuración base
python scripts/seed_maestras_prod.py      # Tipos y categorías del sistema
python scripts/seed_tipos_venta.py        # UNITARIO, PESO_SUELTO, etc
python scripts/seed_tipos_proveedor.py    # CARNES, LACTEOS, etc
python scripts/seed_tipos_documento.py    # Factura, Boleta, etc
python scripts/seed_roles_prod.py         # admin, vendedor, etc
python scripts/seed_menu_rbac.py          # Estructura del menú
```

### Paso 3: Adaptar Datos del Negocio (Por cada cliente)
```bash
# 3.1 Crear locales del nuevo cliente
# Ejemplo: Cliente panadería vs cliente carnicería
INSERT INTO locales (codigo, nombre, direccion, tipo_local_id) VALUES 
('WEB', 'Tienda Online', 'Virtual', 1),
('MATRIZ', 'Local Principal', 'Dirección del cliente', 1);

# 3.2 Crear productos específicos del negocio
# Ejemplo CSV: productos_panaderia.csv vs productos_carniceria.csv

# 3.3 Configurar precios por local

# 3.4 Configurar inventario inicial

# 3.5 Crear usuario admin inicial
python scripts/seed_usuarios_prod.py --email admin@clientenuevo.cl --password admin123
```

### Paso 4: CSVs de Datos de Negocio por Industria

#### 4.1 Panadería/Repostería
```csv
# productos_panaderia.csv
nombre,sku,categoria_codigo,tipo_producto_codigo,precio_web
Pan Amasado,PAN-001,PANADERIA,PRODUCTO_ELABORADO,500
Torta Chocolate,TOR-001,REPOSTERIA,PRODUCTO_ELABORADO,8000
Empanada Pino,EMP-001,PANADERIA,PRODUCTO_ELABORADO,1500
```

#### 4.2 Carnicería
```csv
# productos_carniceria.csv  
nombre,sku,categoria_codigo,tipo_producto_codigo,precio_web
Asado de Tira,CAR-001,CARNES,MATERIA_PRIMA,5500
Pollo Entero,CAR-002,CARNES,MATERIA_PRIMA,2800
Costillar Cerdo,CAR-003,CARNES,MATERIA_PRIMA,4200
```

#### 4.3 Lácteos
```csv
# productos_lacteos.csv
nombre,sku,categoria_codigo,tipo_producto_codigo,precio_web
Queso Gauda,LAC-001,LACTEOS,PRODUCTO_ELABORADO,3500
Leche Entera,LAC-002,LACTEOS,MATERIA_PRIMA,1200
Yogurt Natural,LAC-003,LACTEOS,PRODUCTO_ELABORADO,1800
```

## 🚀 SCRIPT DE AUTOMATIZACIÓN

### deploy_nuevo_cliente.sh
```bash
#!/bin/bash
set -e

CLIENTE_NOMBRE=$1
CLIENTE_EMAIL=$2
CLIENTE_PASSWORD=$3
ARCHIVO_PRODUCTOS=$4

echo "🚀 Iniciando deploy para: $CLIENTE_NOMBRE"

# 1. Seed de sistema base
echo "📋 Configurando sistema base..."
python scripts/seed_maestras_prod.py
python scripts/seed_tipos_venta.py
python scripts/seed_tipos_proveedor.py  
python scripts/seed_tipos_documento.py
python scripts/seed_roles_prod.py
python scripts/seed_menu_rbac.py

# 2. Crear locales base
echo "🏪 Creando locales base..."
python scripts/crear_locales_base.py --nombre "$CLIENTE_NOMBRE"

# 3. Importar productos del cliente
echo "📦 Importando productos..."
python scripts/importar_productos_csv.py --archivo "$ARCHIVO_PRODUCTOS"

# 4. Crear admin inicial
echo "👤 Creando usuario admin..."
python scripts/seed_usuarios_prod.py --email "$CLIENTE_EMAIL" --password "$CLIENTE_PASSWORD"

echo "✅ Deploy completado para $CLIENTE_NOMBRE"
```

### Uso:
```bash
# Deploy para panadería
./deploy_nuevo_cliente.sh "Panadería San Juan" "admin@panaderiasjuan.cl" "admin123" "productos_panaderia.csv"

# Deploy para carnicería  
./deploy_nuevo_cliente.sh "Carnicería Los Andes" "admin@carniceriaandes.cl" "admin123" "productos_carniceria.csv"
```

## 📊 RESUMEN DE ARCHIVOS NECESARIOS

### Por cada tipo de negocio necesitas:
```
/deploy_templates/
├── panaderia/
│   ├── productos_panaderia.csv
│   ├── locales_panaderia.csv  
│   └── precios_panaderia.csv
├── carniceria/
│   ├── productos_carniceria.csv
│   ├── locales_carniceria.csv
│   └── precios_carniceria.csv
└── lacteos/
    ├── productos_lacteos.csv
    ├── locales_lacteos.csv
    └── precios_lacteos.csv
```

## ⚠️ CONSIDERACIONES IMPORTANTES

### Seguridad
- **NUNCA** usar datos de un cliente en el deploy de otro
- Validar que las tablas de negocio estén completamente limpias
- Cambiar todas las credenciales de acceso

### Configuración Específica
- **Local WEB**: Siempre debe existir (codigo='WEB') para landing page
- **Categorías**: Ajustar puntos de fidelidad según el modelo de negocio
- **Tipos de venta**: Validar si el cliente maneja cajas variables o solo productos fijos

### Testing
```bash
# Validar deploy limpio
python scripts/validar_deploy_limpio.py --cliente "Nuevo Cliente"
```

---
**Fecha:** 2026-01-13
**Estado:** Procedimiento definido y listo para implementación