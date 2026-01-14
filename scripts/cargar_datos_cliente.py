# 🔧 Script de Carga de Datos desde CSVs de Cliente

Este script automatiza la carga de todos los datos del cliente desde los CSVs completados.

## 📋 Uso del Script

1. **El cliente completa** todos los CSVs en `csv-templates-clientes/`
2. **Copiamos los CSVs** a la carpeta de la instancia específica
3. **Ejecutamos este script** para cargar todos los datos automáticamente

## 🚀 Comando de Ejecución

```powershell
# Después de crear la instancia y copiar los CSVs
cd fme-backend
.\venv\Scripts\python.exe scripts\cargar_datos_cliente.py --instancia panaderia_cliente1
```

## 📁 Estructura Esperada

```
instances/panaderia_cliente1/data/
├── 1_locales_LLENAR.csv          (completado por cliente)
├── 2_productos_LLENAR.csv        (completado por cliente)  
├── 3_inventario_LLENAR.csv       (completado por cliente)
├── 4_precios_LLENAR.csv          (completado por cliente)
├── 5_usuarios_LLENAR.csv         (completado por cliente)
└── 6_clientes_OPCIONAL.csv       (opcional, completado por cliente)
```

## ⚡ Orden de Carga

El script carga los datos en el orden correcto respetando las dependencias:

1. **Locales** (base para inventario y precios)
2. **Productos** (base para inventario y precios)
3. **Inventario** (requiere locales + productos)
4. **Precios** (requiere locales + productos)
5. **Usuarios** (administradores y vendedores)
6. **Clientes** (si el archivo existe)

## 🛡️ Validaciones Automáticas

- ✅ Verifica que exista el local WEB
- ✅ Valida SKUs únicos
- ✅ Verifica emails únicos
- ✅ Confirma consistencia entre tablas relacionadas
- ✅ Valida formatos de precios y cantidades

## 📊 Reporte Final

Al terminar muestra:
- ✅ Registros cargados por tabla
- ⚠️ Advertencias encontradas
- ❌ Errores críticos
- 📈 Resumen de inventario y precios