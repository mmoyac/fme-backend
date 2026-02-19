# 🗑️ Cómo Eliminar Pedidos de un Tenant

## Opción 1: Modo Interactivo (Recomendado)

Este modo te guía paso a paso y te muestra qué se eliminará antes de hacerlo.

```bash
docker exec -it fme-backend python scripts/eliminar_pedidos_tenant.py
```

El script te pedirá:
1. ✅ Elegir el tenant (te muestra una lista)
2. ✅ Revisar qué se eliminará (modo consulta)
3. ✅ Confirmar escribiendo "CONFIRMAR"

---

## Opción 2: Modo Rápido (Un solo comando)

⚠️ **Cuidado:** Este modo elimina directamente sin mostrar confirmación previa.

```bash
# Para El Olivo
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('El Olivo', confirmar=True)
"

# Para Masas Estación
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('Masas Estación', confirmar=True)
"
```

---

## Opción 3: Solo Ver (No Elimina Nada)

Si solo quieres ver cuántos pedidos hay sin eliminar:

```bash
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('El Olivo', confirmar=False)
"
```

---

## ¿Qué se Elimina Exactamente?

El script elimina **TODO** lo relacionado con los pedidos del tenant:

1. ❌ **Movimientos de inventario** creados por los pedidos
2. ❌ **Items de los pedidos** (productos en cada pedido)
3. ❌ **Movimientos de puntos** asociados a los pedidos
4. ❌ **Pedidos** completos

**NO se elimina:**
- ✅ Clientes (quedan intactos)
- ✅ Productos (quedan intactos)
- ✅ Locales (quedan intactos)
- ✅ Inventario actual (solo los movimientos de pedidos)

---

## 📊 Ver Cuántos Pedidos Tiene Cada Tenant

```bash
docker exec -it fme-backend python -c "
from database.database import SessionLocal
from database.models import Tenant, Pedido, Cliente

db = SessionLocal()
tenants = db.query(Tenant).all()
print('\n📊 PEDIDOS POR TENANT:\n')
for tenant in tenants:
    count = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).count()
    print(f'  {tenant.nombre}: {count} pedidos')
db.close()
"
```

---

## ⚠️ IMPORTANTE: Hacer Backup Antes

**SIEMPRE** haz un backup antes de eliminar datos en producción:

```bash
# Crear backup
docker exec fme-postgres pg_dump -U fme -d fme_database > backup_antes_eliminar.sql

# Si algo sale mal, restaurar desde el backup
docker exec -i fme-postgres psql -U fme -d fme_database < backup_antes_eliminar.sql
```

---

## 📝 Ejemplo Completo de Uso Seguro

```bash
# 1. Hacer backup
echo "📦 Creando backup..."
docker exec fme-postgres pg_dump -U fme -d fme_database > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Ver estado actual
echo "📊 Estado actual:"
docker exec -it fme-backend python -c "
from database.database import SessionLocal
from database.models import Tenant, Pedido, Cliente
db = SessionLocal()
tenants = db.query(Tenant).all()
for tenant in tenants:
    count = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).count()
    print(f'{tenant.nombre}: {count} pedidos')
db.close()
"

# 3. Ejecutar script en modo interactivo
echo "🗑️ Ejecutando eliminación..."
docker exec -it fme-backend python scripts/eliminar_pedidos_tenant.py

# 4. Verificar resultado
echo "✅ Verificando resultado:"
docker exec -it fme-backend python -c "
from database.database import SessionLocal
from database.models import Tenant, Pedido, Cliente
db = SessionLocal()
tenants = db.query(Tenant).all()
for tenant in tenants:
    count = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).count()
    print(f'{tenant.nombre}: {count} pedidos')
db.close()
"
```

---

## 🆘 ¿Algo Salió Mal?

Si algo salió mal y tienes un backup:

```bash
# Restaurar desde backup
docker exec -i fme-postgres psql -U fme -d fme_database < backup_20260217_153045.sql
```

---

## 📞 Contacto

Si tienes dudas o problemas, contacta al equipo de desarrollo.

**Última actualización:** 2026-02-17
