# 📦 Plantillas para Carga de Datos - Masas Estación

Bienvenido al proceso de carga de datos para tu sistema EffiChain.

---

## 📂 Archivos en esta Carpeta

| Archivo | Para qué sirve |
|---------|----------------|
| `REFERENCIA_MAESTRAS.md` | ⭐ **LEE ESTO PRIMERO** - Contiene las categorías, tipos y unidades válidas |
| **Archivos de Referencia del Sistema** | |
| `categorias_sistema.csv` | Las 12 categorías disponibles (IDs 1-12) |
| `tipos_producto_sistema.csv` | Los 4 tipos de producto (IDs 1-4) |
| `unidades_medida_sistema.csv` | Las 10 unidades de medida (IDs 1-10) |
| **Plantillas para Completar** | |
| `productos_ejemplo.csv` | Plantilla para tus productos |
| `locales_ejemplo.csv` | Plantilla para tus sucursales/locales |
| `precios_ejemplo.csv` | Plantilla para precios por local |
| `inventario_inicial_ejemplo.csv` | Plantilla para stock inicial |

---

## 🎯 PASOS A SEGUIR

### 1️⃣ Lee el Documento de Referencia
Abre `REFERENCIA_MAESTRAS.md` y familiarízate con:
- IDs de categorías (1-12)
- IDs de tipos de producto (1-4)
- IDs de unidades de medida (1-10)
- Tipos de locales válidos

También puedes abrir los archivos CSV de referencia del sistema para ver los datos completos.

### 2️⃣ Copia las Plantillas
Crea copias de los archivos ejemplo y renómbralas sin el "_ejemplo":
```
productos_ejemplo.csv → productos.csv
locales_ejemplo.csv → locales.csv
precios_ejemplo.csv → precios.csv
inventario_inicial_ejemplo.csv → inventario_inicial.csv
```

### 3️⃣ Llena tus Datos
Edita los nuevos archivos con tus datos reales. Puedes usar:
- Excel
- Google Sheets
- LibreOffice Calc
- Notepad/VSCode (si conoces CSV)

**Importante:** Guarda siempre como CSV (separado por comas).

### 4️⃣ Orden de Llenado Recomendado

**a) Primero: locales.csv**
- Define tus sucursales
- **OBLIGATORIO:** Incluye un local con código `WEB` para venta online
- Ejemplo:
  ```csv
  codigo,nombre,direccion,telefono,tipo
  WEB,Tienda Online,Santiago,+56912345678,online
  SUC001,Sucursal Centro,Av. Principal 123,+56912345679,sucursal
  ```

**b) Segundo: productos.csv**
- Lista todos tus productos
- Usa los IDs de categorías de `REFERENCIA_MAESTRAS.md`
- SKU debe ser único (ej: PAN-001, MASA-002)
- Ejemplo:
  ```csv
  sku,nombre,descripcion,categoria_id,tipo_producto_id,unidad_medida_id,imagen_url
  PAN-001,Pan Amasado,Pan tradicional,2,2,1,/productos/pan.jpg
  ```
  **Nota:** `tipo_producto_id = 2` es PRODUCTO_ELABORADO (la mayoría de productos de panadería)

**c) Tercero: precios.csv**
- Define el precio de cada producto en cada local
- **CRÍTICO:** Todos los productos deben tener precio en el local WEB
- Ejemplo:
  ```csv
  producto_sku,local_codigo,monto_precio
  PAN-001,WEB,1500
  PAN-001,SUC001,1500
  ```

**d) Cuarto: inventario_inicial.csv**
- Define el stock inicial de cada producto por local
- **NO incluyas el local WEB** (su stock se calcula automático)
- Ejemplo:
  ```csv
  producto_sku,local_codigo,cantidad_stock
  PAN-001,SUC001,100
  PAN-001,BOD001,50
  ```

---

## ✅ VALIDACIÓN ANTES DE ENVIAR

Verifica:
- [ ] Archivo `locales.csv` incluye local con `codigo = WEB`
- [ ] Todos los productos tienen categoría válida (1-12, ver REFERENCIA_MAESTRAS.md)
- [ ] Todos los productos tienen tipo de producto válido (1-4, ver REFERENCIA_MAESTRAS.md)
- [ ] Todos los productos tienen unidad de medida válida (1-10, ver REFERENCIA_MAESTRAS.md)
- [ ] Todos los productos tienen precio en el local WEB
- [ ] Los SKUs de productos son únicos (no se repiten)
- [ ] Los códigos de locales son únicos (no se repiten)
- [ ] Los archivos están guardados como CSV (no XLSX)

---

## 📧 ENVÍO

Una vez completados los 4 archivos, envíalos a:
- **Email:** soporte@effitech.cl
- **Asunto:** "Datos para carga - Masas Estación"

Adjunta los 4 archivos CSV.

---

## ❓ PREGUNTAS FRECUENTES

### ¿Qué pasa si me equivoco en algún dato?
No hay problema, podemos corregirlo antes de subir a producción. Por eso primero lo cargaremos en un entorno de prueba.

### ¿Puedo agregar más productos después?
Sí, el sistema permite agregar productos en cualquier momento desde el Backoffice.

### ¿Debo poner todas mis sucursales?
Solo las que estén activas. Puedes agregar más sucursales después desde el sistema.

### ¿Qué es el local WEB?
Es un local virtual que representa tu tienda online. Sus precios son los que ven los clientes en tu página web. Su stock se calcula automáticamente sumando el stock de tus locales físicos.

### ¿Las imágenes de productos cómo funcionan?
Por ahora puedes poner rutas relativas (ej: `/productos/pan.jpg`). Las imágenes reales las subirás después desde el Backoffice.

---

## 📞 SOPORTE

**EffiChain Support**
- Email: soporte@effitech.cl
- WhatsApp: +56912345678
- Horario: Lunes a Viernes, 9:00 - 18:00

---

**¡Éxito con tu carga de datos!** 🚀
