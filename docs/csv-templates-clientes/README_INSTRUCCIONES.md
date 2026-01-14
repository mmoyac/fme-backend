# 📝 Plantillas CSV para Configuración de Cliente

Este directorio contiene las plantillas CSV que los **clientes** deben llenar con sus datos específicos antes del despliegue de su instancia.

## 📋 Archivos a Completar (en orden)

### 1️⃣ `1_locales_LLENAR.csv` - **OBLIGATORIO**
Define las sucursales y puntos de venta/almacenamiento.

**Campos:**
- `codigo`: Código único del local (sin espacios, mayúsculas)
- `nombre`: Nombre descriptivo del local
- `direccion`: Dirección completa
- `tipo_local_codigo`: VENTA, BODEGA, FRIGORIFICO, PRODUCCION
- `activo`: true/false

### 2️⃣ `2_productos_LLENAR.csv` - **OBLIGATORIO**
Catálogo completo de productos del negocio.

**Campos:**
- `nombre`: Nombre comercial del producto
- `sku`: Código único (ej: PAN-001, CAR-001)
- `descripcion`: Descripción detallada
- `categoria_codigo`: PANADERIA, CARNES, LACTEOS, etc.
- `tipo_producto_codigo`: PRODUCTO_ELABORADO, MATERIA_PRIMA, INSUMO
- `es_vendible`: true si se puede vender
- `es_vendible_web`: true si aparece online
- `stock_minimo`: Cantidad mínima antes de alerta
- `activo`: true/false

### 3️⃣ `3_inventario_LLENAR.csv` - **OBLIGATORIO**
Stock inicial por producto y local.

**Campos:**
- `sku_producto`: SKU del producto (debe existir en productos.csv)
- `codigo_local`: Código del local (debe existir en locales.csv)
- `cantidad_stock`: Cantidad actual en stock

### 4️⃣ `4_precios_LLENAR.csv` - **OBLIGATORIO**
Precios de venta por producto y local.

**Campos:**
- `sku_producto`: SKU del producto
- `codigo_local`: Código del local  
- `monto_precio`: Precio en pesos chilenos (sin formato)

### 5️⃣ `5_usuarios_LLENAR.csv` - **OBLIGATORIO**
Usuarios del sistema (administradores, vendedores).

**Campos:**
- `email`: Email de acceso (único)
- `password`: Contraseña inicial
- `nombre_completo`: Nombre completo
- `rol_codigo`: admin, vendedor, despachador
- `local_defecto_codigo`: Local donde trabaja
- `activo`: true/false

### 6️⃣ `6_clientes_OPCIONAL.csv` - **OPCIONAL**
Base inicial de clientes (si existe).

**Campos:**
- `nombre`: Nombre completo
- `email`: Email del cliente (único)
- `telefono`: Teléfono con formato +56XXXXXXXXX
- `direccion`: Dirección completa
- `comuna`: Comuna
- `activo`: true/false

---

## ✅ Lista de Verificación

**Antes de enviar los CSVs:**

- [ ] **Local WEB definido**: Debe existir un local con código "WEB" para la tienda online
- [ ] **Admin principal**: Al menos un usuario con rol "admin"
- [ ] **SKUs únicos**: No hay SKUs repetidos en productos.csv
- [ ] **Emails únicos**: No hay emails repetidos en usuarios.csv y clientes.csv
- [ ] **Consistencia de códigos**: Todos los códigos de locales y SKUs referenciados existen
- [ ] **Precios WEB**: Todos los productos vendibles tienen precio en el local WEB
- [ ] **Formato números**: Precios sin puntos ni comas (ej: 1500, no $1.500)
- [ ] **Caracteres especiales**: Evitar tildes y ñ en códigos

## 🏪 Ejemplos por Tipo de Negocio

### Panadería
```
Locales: WEB, MATRIZ, SUCURSAL_NORTE, BODEGA
Productos: PAN-001 (Pan Amasado), EMP-001 (Empanada Pino), etc.
Categorías: PANADERIA, PASTELERIA, BEBIDAS
```

### Carnicería
```
Locales: WEB, LOCAL_CENTRO, FRIGORIFICO, BODEGA
Productos: CAR-001 (Asado), POL-001 (Pollo Entero), etc.
Categorías: CARNES, AVES, EMBUTIDOS, CONGELADOS
```

### Lácteos
```
Locales: WEB, DISTRIBUCION, FRIGORIFICO_A, FRIGORIFICO_B
Productos: LEC-001 (Leche Entera), QUE-001 (Queso Gauda), etc.
Categorías: LACTEOS, QUESOS, YOGURT, MANTEQUILLAS
```

### Retail General
```
Locales: WEB, TIENDA, BODEGA
Productos: ALI-001 (Aceite), CON-001 (Arroz), etc.
Categorías: CONSERVAS, ACEITES, CONDIMENTOS, DESCARTABLES
```

## 📞 Soporte

Si tiene dudas completando los CSVs, contacte al equipo técnico con:
1. Tipo de negocio
2. Archivo específico con dudas
3. Número de productos/locales aproximado

**¡Los datos completos y correctos garantizan un despliegue exitoso!**