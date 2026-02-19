from database.database import SessionLocal
from database.models import Pedido, Despacho, Tenant

db = SessionLocal()

# Buscar tenant El Olivo
tenant = db.query(Tenant).filter(Tenant.id == 2).first()
print(f'Tenant: {tenant.nombre if tenant else "No encontrado"}')
print()

# Buscar pedidos CONFIRMADOS del tenant 2
pedidos = db.query(Pedido).filter(
    Pedido.tenant_id == 2,
    Pedido.estado_id == 2  # CONFIRMADO
).all()

print(f'Total pedidos CONFIRMADOS tenant 2: {len(pedidos)}')
print()

for pedido in pedidos:
    despacho = db.query(Despacho).filter(Despacho.pedido_id == pedido.id).first()
    print(f'Pedido #{pedido.id} ({pedido.numero_pedido}):')
    print(f'  Cliente: {pedido.cliente.nombre if pedido.cliente else "Sin cliente"}')
    print(f'  Estado: {pedido.estado_pedido.codigo if pedido.estado_pedido else "Sin estado"}')
    print(f'  Total: ${pedido.monto_total}')
    print(f'  Despacho: {f"ID {despacho.id} - {despacho.estado}" if despacho else "No asignado"}')
    print()
