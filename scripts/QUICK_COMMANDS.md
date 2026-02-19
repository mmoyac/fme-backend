# 🚀 Atajos para Scripts Comunes

## Eliminar Pedidos de un Tenant (Modo Rápido)

### El Olivo
```bash
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('El Olivo', confirmar=True)
"
```

### Masas Estación
```bash
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('Masas Estación', confirmar=True)
"
```

---

## Solo Consultar (Sin Eliminar)

### Ver pedidos de El Olivo sin eliminar
```bash
docker exec -it fme-backend python -c "
from scripts.eliminar_pedidos_tenant import eliminar_pedidos_tenant
eliminar_pedidos_tenant('El Olivo', confirmar=False)
"
```

---

## Verificar Pedidos Actuales

```bash
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

## Backup Rápido de Base de Datos

```bash
# Crear backup con timestamp
docker exec fme-postgres pg_dump -U fme -d fme_database > "backup_$(date +%Y%m%d_%H%M%S).sql"

# Restaurar desde backup
docker exec -i fme-postgres psql -U fme -d fme_database < backup_20260217_153045.sql
```

---

## Copiar Scripts al Contenedor (Si es necesario)

```bash
# Si el script no está en el contenedor, puedes copiarlo
docker cp scripts/eliminar_pedidos_tenant.py fme-backend:/app/scripts/
```
