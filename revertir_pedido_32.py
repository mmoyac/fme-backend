"""Revertir pedido E-2026-00032 a EN_PREPARACION."""
from database.database import SessionLocal
from database.models import Pedido, Cliente, EstadoPedido

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00032'
).first()

if not pedido:
    print("❌ Pedido no encontrado")
    db.close()
    exit()

# Obtener el estado EN_PREPARACION
estado_prep = db.query(EstadoPedido).filter(
    EstadoPedido.codigo == 'EN_PREPARACION'
).first()

if not estado_prep:
    print("❌ Estado EN_PREPARACION no encontrado")
    db.close()
    exit()

estado_actual = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"🔄 Revirtiendo pedido {pedido.numero_pedido}")
print(f"   Estado actual: {estado_actual.nombre}")
print(f"   → Nuevo estado: EN_PREPARACION")

pedido.estado_id = estado_prep.id
db.commit()

print(f"✅ Pedido revertido exitosamente")

db.close()
