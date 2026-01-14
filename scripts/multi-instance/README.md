# 🚀 QUICK START - SISTEMA MULTI-INSTANCIA

## Comandos Esenciales

### Crear y Levantar Demo de Panadería:
```bash
cd fme-backend
.\scripts\multi-instance\gestionar_instancias.ps1 -Accion crear -Tipo panaderia
.\scripts\multi-instance\gestionar_instancias.ps1 -Accion levantar -Tipo panaderia
```

### Ver Estado:
```bash
.\scripts\multi-instance\gestionar_instancias.ps1 -Accion estado
```

### URLs de Acceso:
- **Panadería:** Backend: 8000, Landing: 3000, Backoffice: 3001
- **Carnicería:** Backend: 8002, Landing: 3002, Backoffice: 3003  
- **Lácteos:** Backend: 8004, Landing: 3004, Backoffice: 3005

### Documentación Completa:
📖 [MULTI_INSTANCIA_GITHUB.md](docs/MULTI_INSTANCIA_GITHUB.md)