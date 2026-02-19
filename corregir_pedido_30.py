from database.database import SessionLocal
from database.models import Pedido, Cliente, EstadoPedido

db = SessionLocal()

# Buscar el pedido
pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00030'
).first()

if not pedido:
    print("❌ Pedido no encontrado")
    exit()

# Obtener el estado ENTREGADO
estado_entregado = db.query(EstadoPedido).filter(
    EstadoPedido.codigo == 'ENTREGADO'
).first()

if not estado_entregado:
    print("❌ Estado ENTREGADO no encontrado")
    exit()

estado_actual = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"=== CORRIGIENDO PEDIDO {pedido.numero_pedido} ===\n")
print(f"Estado actual: {estado_actual.nombre} (ID: {estado_actual.id})")
print(f"Nuevo estado: {estado_entregado.nombre} (ID: {estado_entregado.id})")

# Actualizar el estado
pedido.estado_id = estado_entregado.id

db.commit()

print(f"\n✅ Pedido actualizado exitosamente")
print(f"   {pedido.numero_pedido} → Estado: ENTREGADO")

# Verificar
db.refresh(pedido)
estado_final = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"\n📋 VERIFICACIÓN:")
print(f"   Estado actual: {estado_final.nombre}")
print(f"   Despacho: {pedido.despacho.estado_despacho if pedido.despacho else 'Sin despacho'}")

db.close()
