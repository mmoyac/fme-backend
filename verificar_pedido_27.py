from database.database import SessionLocal
from database.models import Pedido, ItemPedido, Lote, Cliente, EstadoPedido

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00027'
).first()

if not pedido:
    print("Pedido no encontrado")
    exit()

estado = db.query(EstadoPedido).filter(EstadoPedido.id == pedido.estado_id).first()

print(f"=== PEDIDO {pedido.numero_pedido} ===")
print(f"Tipo: {pedido.tipo_pedido.codigo if pedido.tipo_pedido else 'N/A'}")
print(f"Estado: {estado.nombre if estado else 'N/A'}")
print(f"\nItems del pedido:")

for item in pedido.items:
    print(f"\n  - Producto: {item.producto.nombre}")
    print(f"    SKU: {item.producto.sku}")
    print(f"    Cantidad: {item.cantidad}")
    print(f"    Lote ID: {item.lote_id}")
    
    if item.lote_id:
        lote = db.query(Lote).filter(Lote.id == item.lote_id).first()
        if lote:
            print(f"    Lote codigo: {lote.codigo_lote}")
            print(f"    Peso actual: {lote.peso_actual} kg")
        else:
            print(f"    [ERROR] Lote con ID {item.lote_id} no encontrado")
    else:
        print(f"    [PROBLEMA] Sin lote asignado (debería tener uno si es CAJAS_VARIABLES)")

db.close()
