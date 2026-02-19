# 📊 GUÍA DE RECOLECCIÓN DE DATOS - MASAS ESTACIÓN

## Datos a Solicitar al Cliente

### 1️⃣ PRODUCTOS (Excel/CSV)
Template: `productos.csv`

| SKU | Nombre | Descripción | Categoría | Precio Venta | Unidad | Imagen URL |
|-----|--------|-------------|-----------|--------------|--------|------------|
| PAN-001 | Pan Amasado | Pan tradicional chileno | Panadería | 1500 | unidad | url_imagen |
| EMP-001 | Empanada de Pino | Empanada casera | Empanadas | 2500 | unidad | url_imagen |

**Columnas obligatorias:**
- `SKU` (único, ej: PAN-001)
- `Nombre`
- `Categoria` (debe existir en categorías)
- `Precio Venta` (precio para local WEB)

**Columnas opcionales:**
- `Descripcion`
- `Unidad` (unidad, kg, docena, etc.)
- `Imagen URL`
- `Ganancia Puntos` (puntos por producto, default por categoría)

---

### 2️⃣ INVENTARIO INICIAL (Excel/CSV)
Template: `inventario_inicial.csv`

| SKU | Local | Stock Inicial |
|-----|-------|---------------|
| PAN-001 | MATRIZ | 100 |
| PAN-001 | SUCURSAL1 | 50 |
| EMP-001 | MATRIZ | 80 |

**Notas:**
- No incluir local "WEB" (es virtual)
- Stock del local WEB se calcula automáticamente (suma de todos)

---

### 3️⃣ PROVEEDORES (Excel/CSV)
Template: `proveedores.csv`

| RUT | Nombre | Email | Teléfono | Dirección |
|-----|--------|-------|----------|-----------|
| 12345678-9 | Molinos SA | contacto@molinos.cl | +56912345678 | Santiago |

---

### 4️⃣ LOCALES/SUCURSALES (Excel/CSV)
Template: `locales.csv`

| Codigo | Nombre | Dirección | Teléfono |
|--------|--------|-----------|----------|
| MATRIZ | Casa Matriz | Av. Principal 123 | +56912345678 |
| SUCURSAL1 | Sucursal Providencia | Pedro de Valdivia 456 | +56987654321 |

**Nota:** NO incluir local 'WEB' (ya existe)

---

### 5️⃣ CLIENTES EXISTENTES (Opcional)
Template: `clientes.csv`

| Nombre | Email | Teléfono | Dirección | Comuna | Puntos Iniciales |
|--------|-------|----------|-----------|--------|------------------|
| Juan Pérez | juan@example.com | +56912345678 | Calle 123 | Santiago | 0 |

---

### 6️⃣ CONFIGURACIÓN DE LANDING (Formulario Web)

Solicitar vía backoffice en:
`https://admin.masasestacion.cl/admin/configuracion-landing`

**Datos a configurar:**
- Logo (PNG/JPG)
- Favicon (ICO/PNG)
- Colores corporativos (hex)
- Textos del hero
- Beneficios (3-4 ítems)
- Redes sociales (Facebook, Instagram, WhatsApp)
- Datos de contacto (teléfono, email, dirección)

---

## 📁 Formato de Entrega

**Opción 1: Excel con múltiples hojas**
```
datos_masas_estacion.xlsx
├─ Hoja 1: Productos
├─ Hoja 2: Inventario
├─ Hoja 3: Proveedores
├─ Hoja 4: Locales
└─ Hoja 5: Clientes
```

**Opción 2: Carpeta con CSVs**
```
datos_masas_estacion/
├─ productos.csv
├─ inventario_inicial.csv
├─ proveedores.csv
├─ locales.csv
└─ clientes.csv
```

---

## ⚠️ IMPORTANTE

1. **No enviar datos sensibles** (contraseñas de clientes, datos bancarios)
2. **SKUs únicos:** No pueden repetirse
3. **Categorías:** Deben corresponder a las existentes en el sistema
4. **Codificación:** UTF-8 para evitar problemas con tildes/ñ
5. **Imágenes:** URLs públicas o se suben después manualmente

---

## 🔄 Proceso de Importación

1. **Validación:** Sistema valida datos (SKUs únicos, categorías válidas, etc.)
2. **Staging:** Se importa primero en ambiente de desarrollo
3. **Revisión:** Cliente revisa datos en desarrollo
4. **Producción:** Se migra a producción (sin borrar datos existentes)

---

**Última actualización:** 2026-02-19
