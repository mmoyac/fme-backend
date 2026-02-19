# 📚 REFERENCIA DE MAESTRAS - Sistema EffiChain

Este documento contiene los valores válidos que debes usar al llenar los archivos CSV.

---

## 🏷️ CATEGORÍAS DE PRODUCTOS

Usa el **ID** exacto en la columna `categoria_id` de `productos.csv`:

| ID | Código | Nombre | Descripción | Puntos Ganados |
|----|--------|--------|-------------|----------------|
| 1 | GENERAL | General | Categoría general por defecto | Sin puntos |
| 2 | PANADERIA | Panadería | Productos de panadería | 10 puntos |
| 3 | PASTELERIA | Pastelería | Productos de pastelería | 15 puntos |
| 4 | EMPANADAS | Empanadas | Empanadas y productos salados | 12 puntos |
| 5 | LACTEOS | Lácteos | Quesos, mantequilla, etc | 8 puntos |
| 6 | ABARROTES | Abarrotes | Productos de abarrotes | 5 puntos |
| 7 | CARNES | CARNES | Ventas por caja | Sin puntos |
| 8 | QUESOS | QUESOS | - | Sin puntos |
| 9 | PIZZA | pizza | - | Sin puntos |
| 10 | QUESOS_Unidad | QUESOS_Unidad | - | Sin puntos |
| 11 | ACEITE | ACEITE | - | Sin puntos |
| 12 | PAPAS | PAPAS | - | Sin puntos |

**Ejemplo:** Si vendes "Pan Amasado", usa `categoria_id = 2` (PANADERIA)

---

## 🏭 TIPOS DE PRODUCTO

Usa el **ID** exacto en la columna `tipo_producto_id` de `productos.csv`:

| ID | Código | Nombre | Descripción | Cuándo usar |
|----|--------|--------|-------------|-------------|
| 1 | MATERIA_PRIMA | Materia Prima | Productos comprados para uso/venta | Harina, levadura, ingredientes que compras |
| 2 | PRODUCTO_ELABORADO | Producto Elaborado | Productos fabricados internamente | Pan, empanadas, pasteles que produces |
| 3 | INSUMO | Insumo | Materiales no vendibles | Envases, bolsas, cajas (no son para venta) |
| 4 | SERVICIO | Servicio | Servicios ofrecidos | Delivery, catering, servicios varios |

**Ejemplo:** Si produces "Pan Amasado" en tu local, usa `tipo_producto_id = 2` (PRODUCTO_ELABORADO)

**Importante:** La mayoría de productos de panadería/pastelería son tipo 2 (PRODUCTO_ELABORADO).

---

## 📏 UNIDADES DE MEDIDA

Usa el **ID** exacto en la columna `unidad_medida_id` de `productos.csv`:

| ID | Código | Nombre | Símbolo | Tipo | Factor | Cuándo usar |
|----|--------|--------|---------|------|--------|-------------|
| 1 | UNIDAD | Unidad | un | CANTIDAD | 1.0 | Productos individuales (pan, empanada) |
| 2 | KILOGRAMO | Kilogramo | kg | PESO | 1.0 | Productos por peso (masa, queso) |
| 3 | GRAMO | Gramo | g | PESO | 1000.0 | Productos pequeños por peso |
| 4 | LITRO | Litro | L | VOLUMEN | 1.0 | Líquidos en litros |
| 5 | MILILITRO | Mililitro | ml | VOLUMEN | 1000.0 | Líquidos pequeños |
| 6 | DOCENA | Docena | doc | CANTIDAD | 12.0 | 12 unidades (hallullas x12) |
| 7 | MEDIA_DOCENA | Media Docena | 1/2 doc | CANTIDAD | 6.0 | 6 unidades |
| 8 | CAJA | Caja | caja | CANTIDAD | 1.0 | Productos en caja |
| 9 | PAQUETE | Paquete | paq | CANTIDAD | 1.0 | Productos empaquetados |
| 10 | bandeja | bandeja | b | CANTIDAD | 30.0 | Bandejas (30 unidades) |

**Ejemplo:** Si vendes "Pan Amasado" por unidad, usa `unidad_medida_id = 1`

**Nota:** El factor indica cuántas unidades base equivalen a esta medida (ej: 1000 gr = 1 kg)

---

## 🏪 TIPOS DE LOCALES

Usa estos valores en la columna `tipo` de `locales.csv`:

| Código | Descripción |
|--------|-------------|
| `sucursal` | Local físico/sucursal con atención presencial |
| `online` | Tienda online (solo para local WEB) |
| `bodega` | Bodega/almacén sin venta directa |

**Importante:** 
- El local con `codigo = WEB` DEBE tener `tipo = online`
- Este es el local que define los precios públicos de la landing page

---

## 📋 EJEMPLO COMPLETO

### productos.csv
```csv
sku,nombre,descripcion,categoria_id,tipo_producto_id,unidad_medida_id,imagen_url
PAN-001,Pan Amasado,Pan amasado tradicional chileno,2,2,1,/productos/pan-amasado.jpg
MASA-001,Masa de Empanada,Masa de hojaldre para empanadas,2,2,2,/productos/masa-empanada.jpg
EMP-001,Empanada de Pino,Empanada de carne jugosa,4,2,1,/productos/empanada-pino.jpg
```

**Nota:** 
- `categoria_id = 2` es PANADERIA (para pan y masas)
- `categoria_id = 4` es EMPANADAS
- `tipo_producto_id = 2` es PRODUCTO_ELABORADO (productos que fabricas)
- `unidad_medida_id = 1` es UNIDAD (para productos individuales)
- `unidad_medida_id = 2` es KILOGRAMO (para ventas por peso)

### locales.csv
```csv
codigo,nombre,direccion,telefono,tipo
WEB,Tienda Online,Santiago Centro,+56912345678,online
SUC001,Sucursal Centro,Av. Libertad 123,+56912345679,sucursal
BOD001,Bodega Principal,Calle Industrial 456,+56912345680,bodega
```

### precios.csv
```csv
producto_sku,local_codigo,monto_precio
PAN-001,WEB,1500
PAN-001,SUC001,1500
MASA-001,WEB,3500
MASA-001,SUC001,3200
EMP-001,WEB,2000
EMP-001,SUC001,2000
```

### inventario_inicial.csv
```csv
producto_sku,local_codigo,cantidad_stock
PAN-001,SUC001,100
PAN-001,BOD001,50
MASA-001,SUC001,20
MASA-001,BOD001,30
EMP-001,SUC001,80
```

**Nota:** El local WEB NO tiene stock físico. Su stock se calcula automáticamente como la suma de todos los locales físicos.

---

## ✅ CHECKLIST ANTES DE ENVIAR

- [ ] Todos los productos tienen `categoria_id` entre 1 y 6
- [ ] Todas las unidades de medida son válidas (unidad, kg, docena, paquete, caja)
- [ ] Existe un local con `codigo = WEB` y `tipo = online`
- [ ] Todos los productos tienen precio en el local WEB
- [ ] Los SKUs no se repiten (son únicos)
- [ ] Los códigos de locales no se repiten (son únicos)

---

## 📞 SOPORTE

Si tienes dudas al llenar los CSVs, contacta a EffiChain:
- Email: soporte@effitech.cl
- WhatsApp: +56912345678

---

**Versión:** 1.0  
**Fecha:** Febrero 2026
