# 🏢 SISTEMA MULTI-INSTANCIA - MÚLTIPLES NEGOCIOS

## 🎯 CONCEPTO

Sistema para crear **instancias independientes y aisladas** del ecommerce, donde cada tipo de negocio tiene:
- ✅ Backend propio con BD independiente
- ✅ Backoffice propio para gestión
- ✅ Landing propia para ventas (opcional)
- ✅ Puertos únicos y configuración aislada
- ✅ Datos específicos del tipo de negocio

## 🏗️ ARQUITECTURA MULTI-INSTANCIA

```
Instancias Locales de Desarrollo:
┌─────────────────────────────────────┐
│  PANADERÍA (Instancia 1)            │
│  Backend: localhost:8000             │
│  Backoffice: localhost:3001          │
│  Landing: localhost:3000             │
│  BD: fme_panaderia                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  CARNICERÍA (Instancia 2)           │
│  Backend: localhost:8002             │
│  Backoffice: localhost:3003          │
│  Landing: localhost:3002             │
│  BD: fme_carniceria                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  LÁCTEOS (Instancia 3)              │
│  Backend: localhost:8004             │
│  Backoffice: localhost:3005          │
│  Landing: localhost:3004             │
│  BD: fme_lacteos                     │
└─────────────────────────────────────┘
```

## 📊 MAPEO DE PUERTOS

| Tipo Negocio | Backend | Landing | Backoffice | Base de Datos |
|--------------|---------|---------|------------|---------------|
| **panaderia** | 8000 | 3000 | 3001 | fme_panaderia |
| **carniceria** | 8002 | 3002 | 3003 | fme_carniceria |
| **lacteos** | 8004 | 3004 | 3005 | fme_lacteos |
| **empanadas** | 8006 | 3006 | 3007 | fme_empanadas |
| **mariscos** | 8008 | 3008 | 3009 | fme_mariscos |

## 🚀 COMANDOS RÁPIDOS

### Crear Nueva Instancia
```bash
# Crear instancia completa de panadería
.\scripts\crear_instancia.ps1 -Tipo "panaderia" -Nombre "Panadería Artesanal"

# Crear instancia completa de carnicería  
.\scripts\crear_instancia.ps1 -Tipo "carniceria" -Nombre "Carnes Premium"
```

### Levantar Instancia Específica
```bash
# Solo panadería
.\scripts\levantar_instancia.ps1 -Tipo "panaderia"

# Solo carnicería
.\scripts\levantar_instancia.ps1 -Tipo "carniceria"

# Todas las instancias
.\scripts\levantar_todas_instancias.ps1
```

### Parar Instancia Específica
```bash
# Parar solo panadería
.\scripts\parar_instancia.ps1 -Tipo "panaderia"

# Parar todas
.\scripts\parar_todas_instancias.ps1
```

## 📁 ESTRUCTURA DE DIRECTORIOS

```
ProyectosAI/Masas_Estacion/
├── fme-backend/                    # Backend base/template
├── fme-backoffice/                 # Backoffice base/template  
├── fme-landing/                    # Landing base/template
├── instancias/                     # Instancias específicas
│   ├── panaderia/
│   │   ├── docker-compose.yml     # Configuración específica
│   │   ├── .env.panaderia         # Variables específicas
│   │   ├── data/                  # Datos específicos
│   │   │   ├── productos.csv
│   │   │   ├── locales.csv
│   │   │   └── inventario.csv
│   │   └── volumes/               # Volúmenes Docker
│   │       └── postgres_data/
│   ├── carniceria/
│   │   ├── docker-compose.yml
│   │   ├── .env.carniceria
│   │   ├── data/
│   │   └── volumes/
│   └── lacteos/
│       ├── docker-compose.yml
│       ├── .env.lacteos
│       ├── data/
│       └── volumes/
└── scripts/                       # Scripts de gestión
    ├── crear_instancia.ps1
    ├── levantar_instancia.ps1
    └── gestionar_instancias.ps1
```

## 🐳 DOCKER COMPOSE POR INSTANCIA

Cada instancia tiene su propio `docker-compose.yml` con:
- Puertos únicos
- Base de datos independiente  
- Variables de entorno específicas
- Volúmenes aislados

## 📋 CASOS DE USO

### Desarrollo Paralelo
```bash
# Desarrollador 1 trabaja en panadería
.\scripts\levantar_instancia.ps1 -Tipo "panaderia"
# URLs: localhost:8000, localhost:3000, localhost:3001

# Desarrollador 2 trabaja en carnicería  
.\scripts\levantar_instancia.ps1 -Tipo "carniceria"
# URLs: localhost:8002, localhost:3002, localhost:3003
```

### Demostración a Clientes
```bash
# Demo para cliente panadería
.\scripts\levantar_instancia.ps1 -Tipo "panaderia"
# Mostrar productos específicos, precios, flujo completo

# Demo para cliente carnicería
.\scripts\parar_instancia.ps1 -Tipo "panaderia"
.\scripts\levantar_instancia.ps1 -Tipo "carniceria" 
# Cambiar a productos cárnicos, precios diferentes
```

### Testing de Configuraciones
```bash
# Probar configuración A en panadería
.\scripts\levantar_instancia.ps1 -Tipo "panaderia" -Config "config_a"

# Probar configuración B en lácteos
.\scripts\levantar_instancia.ps1 -Tipo "lacteos" -Config "config_b"
```

---

**Estado:** 🔧 **En construcción**  
**Próximo paso:** Crear scripts de automatización