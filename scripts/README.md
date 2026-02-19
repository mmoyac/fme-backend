# 📜 Scripts de Mantenimiento - FME Backend

Esta carpeta contiene scripts útiles para el mantenimiento y operaciones administrativas de la base de datos del sistema FME.

## 🗂️ Scripts Disponibles

### 1. `eliminar_pedidos_tenant.py`

Elimina todos los pedidos de un tenant específico, incluyendo sus datos relacionados.

**Uso desde contenedor Docker:**
```bash
docker exec -it fme-backend python scripts/eliminar_pedidos_tenant.py
```

**Uso directo (si estás en el entorno local):**
```bash
cd fme-backend
python scripts/eliminar_pedidos_tenant.py
```

**Características:**
- ✅ Eliminación segura respetando integridad referencial
- ✅ Modo consulta para ver qué se eliminará antes de confirmar
- ✅ Confirmación explícita requerida
- ✅ Muestra resumen detallado antes de ejecutar
- ✅ Elimina en cascada: movimientos de inventario, items, movimientos de puntos y pedidos

**Uso programático:**
```python
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant

# Modo consulta (no elimina, solo muestra información)
resultado = eliminar_pedidos_tenant("El Olivo", confirmar=False)

# Modo ejecución (elimina con confirmación interactiva)
resultado = eliminar_pedidos_tenant("El Olivo", confirmar=True)
```

**Orden de eliminación:**
1. Movimientos de inventario (tipo PEDIDO y AJUSTE)
2. Items de pedidos
3. Movimientos de puntos
4. Pedidos

**Ejemplo de salida:**
```
============================================================
SCRIPT DE ELIMINACIÓN DE PEDIDOS POR TENANT
============================================================

Tenants disponibles:
  1. Masas Estación (ID: 1)
  2. El Olivo (ID: 2)

============================================================
Ingresa el nombre exacto del tenant: El Olivo

🔍 MODO CONSULTA - Analizando pedidos...

✅ Tenant encontrado: El Olivo (ID: 2)
============================================================

📊 Total de pedidos a eliminar: 15

📋 Muestra de pedidos (primeros 5):
   1. Pedido #PED-00001 - Cliente: Juan Pérez - Total: $5000 - Estado: ENTREGADO
   2. Pedido #PED-00002 - Cliente: María González - Total: $8500 - Estado: CONFIRMADO
   3. Pedido #PED-00003 - Cliente: Pedro Soto - Total: $3200 - Estado: PENDIENTE
   4. Pedido #PED-00004 - Cliente: Ana López - Total: $12000 - Estado: ENTREGADO
   5. Pedido #PED-00005 - Cliente: Carlos Díaz - Total: $6500 - Estado: CANCELADO
   ... y 10 pedidos más

📦 Registros relacionados a eliminar:
   - Items de pedidos: 45
   - Movimientos de inventario: 12
   - Movimientos de puntos: 8
============================================================

⚠️  MODO CONSULTA: No se eliminarán registros.
   Para ejecutar la eliminación, llama al script con confirmar=True
```

---

## ⚠️ Precauciones Importantes

### Antes de Ejecutar Cualquier Script:

1. **Backup de Base de Datos:**
   ```bash
   docker exec fme-postgres pg_dump -U fme -d fme_database > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Verificar el Tenant Correcto:**
   - Usa el modo consulta primero
   - Verifica los nombres de los tenants disponibles
   - Los nombres son case-sensitive

3. **Entorno de Producción:**
   - Ejecuta primero en desarrollo/staging
   - Coordina con el equipo antes de ejecutar
   - Mantén un log de las operaciones realizadas

---

## 🔧 Comandos Útiles de Docker

### Ver logs del backend:
```bash
docker logs fme-backend --tail 50 -f
```

### Acceder a la consola Python del backend:
```bash
docker exec -it fme-backend python
```

### Acceder a PostgreSQL:
```bash
docker exec -it fme-postgres psql -U fme -d fme_database
```

### Verificar pedidos de un tenant (SQL):
```sql
SELECT 
    t.nombre as tenant,
    COUNT(p.id) as total_pedidos,
    SUM(p.monto_total) as total_ventas
FROM pedidos p
JOIN clientes c ON p.cliente_id = c.id
JOIN tenants t ON c.tenant_id = t.id
GROUP BY t.nombre;
```

---

## 📝 Plantilla para Nuevos Scripts

```python
#!/usr/bin/env python
"""
Descripción breve del script.

Uso:
    docker exec -it fme-backend python scripts/nombre_script.py

Autor: Sistema FME
Fecha: YYYY-MM-DD
"""

from database.database import SessionLocal
from database.models import *

def main():
    db = SessionLocal()
    try:
        # Tu código aquí
        pass
    except Exception as e:
        db.rollback()
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == '__main__':
    main()
```

---

## 🆘 Soporte

Si tienes problemas con algún script:
1. Verifica que el contenedor Docker esté corriendo
2. Revisa los logs del backend
3. Asegúrate de tener los permisos necesarios
4. Contacta al equipo de desarrollo

---

**Última actualización:** 2026-02-17
