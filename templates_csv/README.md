# 🚀 Onboarding de Nuevos Tenants mediante CSV

Este sistema permite crear un nuevo tenant (empresa) completo cargando archivos CSV con la información inicial.

## 📋 Archivos CSV Requeridos

### 1. `tenant_config.csv` - Configuración del Tenant
Información básica de la empresa y configuración de la landing page.

**Campos:**
- `codigo` (obligatorio): Código único del tenant (ej: TENANT3, EMPRESA1)
- `nombre` (obligatorio): Nombre completo de la empresa
- `nombre_comercial` (obligatorio): Nombre comercial para mostrar
- `dominio_principal` (obligatorio): Dominio principal (ej: minuevaempresa.cl)
- `subdomain` (opcional): Subdominio (ej: minuevaempresa)
- `color_primario`: Color principal en hex (ej: #3b82f6)
- `color_secundario`: Color secundario en hex
- `color_acento`: Color de acento en hex
- `hero_titulo`: Título del hero section
- `hero_subtitulo`: Subtítulo del hero section
- `telefono`: Teléfono de contacto
- `email`: Email de contacto
- `direccion`: Dirección física
- `logo_url`: URL del logo (opcional)
- `favicon_url`: URL del favicon (opcional)

### 2. `locales.csv` - Locales de Venta
**IMPORTANTE:** Debe incluir un local con código `WEB` (obligatorio para e-commerce).

**Campos:**
- `codigo` (obligatorio): Código único (ej: WEB, SUC01, SUC02)
- `nombre` (obligatorio): Nombre del local
- `direccion`: Dirección física
- `telefono`: Teléfono del local

**Ejemplo:**
```csv
codigo,nombre,direccion,telefono
WEB,Tienda Online,www.empresa.cl,
SUC01,Sucursal Centro,Av. Principal 123,+56912345678
```

### 3. `productos.csv` - Catálogo de Productos

**Campos:**
- `sku` (obligatorio): Código único del producto
- `nombre` (obligatorio): Nombre del producto
- `descripcion`: Descripción del producto
- `categoria_id` (obligatorio): ID de categoría (consultar con admin)
- `tipo_producto_id` (obligatorio): ID de tipo (consultar con admin)
- `unidad_medida_id` (obligatorio): ID de unidad (consultar con admin)
- `precio_compra`: Precio de compra (opcional)
- `costo_fabricacion`: Costo de fabricación (opcional)
- `stock_minimo`: Stock mínimo (default: 0)
- `stock_critico`: Stock crítico (default: 0)
- `es_vendible`: true/false (default: true)
- `es_vendible_web`: true/false (default: true)
- `es_ingrediente`: true/false (default: false)

**IDs comunes:**
- `categoria_id`: 1=Panadería, 2=Pastelería, 3=Bebidas (verificar con admin)
- `tipo_producto_id`: 1=Producto Terminado, 2=Materia Prima
- `unidad_medida_id`: 1=Unidad, 2=Kilogramo, 3=Gramo

### 4. `precios.csv` - Precios por Local
**IMPORTANTE:** Cada producto DEBE tener precio en el local `WEB` para aparecer en el catálogo online.

**Campos:**
- `sku` (obligatorio): SKU del producto
- `codigo_local` (obligatorio): Código del local
- `precio` (obligatorio): Precio de venta (en pesos chilenos, sin decimales)

**Ejemplo:**
```csv
sku,codigo_local,precio
PROD-001,WEB,5000
PROD-001,SUC01,5000
PROD-001,SUC02,4800
```

### 5. `inventario.csv` - Stock Inicial
**NOTA:** El local `WEB` NO debe tener inventario. El stock se suma de los locales físicos.

**Campos:**
- `sku` (obligatorio): SKU del producto
- `codigo_local` (obligatorio): Código del local físico
- `stock` (obligatorio): Cantidad inicial

**Ejemplo:**
```csv
sku,codigo_local,stock
PROD-001,SUC01,100
PROD-001,SUC02,80
```

### 6. `usuarios.csv` - Usuarios del Sistema

**Campos:**
- `email` (obligatorio): Email del usuario (único)
- `nombre_completo` (obligatorio): Nombre completo
- `password` (obligatorio): Contraseña temporal
- `role_id` (obligatorio): 1=Admin, 2=Vendedor, 3=Despachador
- `local_defecto_codigo`: Código del local asignado

**Ejemplo:**
```csv
email,nombre_completo,password,role_id,local_defecto_codigo
admin@empresa.cl,Administrador,admin123,1,SUC01
vendedor@empresa.cl,Vendedor,vendedor123,2,SUC01
```

---

## 🎯 Proceso de Importación

### Opción 1: Línea de Comandos (Recomendado para desarrollo)

1. **Preparar archivos CSV** en una carpeta:
```
tenant_data/
├── tenant_config.csv
├── locales.csv
├── productos.csv
├── precios.csv
├── inventario.csv
└── usuarios.csv
```

2. **Ejecutar script de importación:**
```bash
cd fme-backend
docker-compose exec backend python scripts/import_tenant_csv.py --folder ./tenant_data/
```

3. **Verificar resultado:**
El script mostrará un resumen de lo importado.

### Opción 2: Interfaz Web (Próximamente)

Se creará una interfaz en el backoffice para subir los archivos CSV directamente.

---

## ✅ Validaciones del Sistema

El script validará automáticamente:

1. ✅ Existencia del local `WEB` (obligatorio)
2. ✅ SKUs únicos en productos
3. ✅ Referencias válidas entre tablas (productos → categorías, etc.)
4. ✅ Emails únicos en usuarios
5. ✅ Formato correcto de datos

Si hay errores, el script los mostrará y NO creará el tenant.

---

## 📦 Templates Disponibles

Los templates de ejemplo están en:
```
fme-backend/templates_csv/
```

Puedes descargarlos y modificarlos con tus datos.

---

## 🔐 Seguridad

- Las contraseñas en `usuarios.csv` se hashean automáticamente con Argon2
- Los usuarios deben cambiar su contraseña temporal al primer login
- Los códigos de tenant deben ser únicos en el sistema

---

## 📞 Soporte

Si tienes dudas sobre:
- IDs de categorías, tipos o unidades disponibles
- Formato de datos
- Errores en la importación

Contacta al administrador del sistema.
