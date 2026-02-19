from database.database import SessionLocal
from database.models import Pedido, ItemPedido, Lote, Cliente, PickingItem

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00028'
).first()

if not pedido:
    print("Pedido no encontrado")
    exit()

print(f"=== VERIFICACION PEDIDO {pedido.numero_pedido} ===\n")
print(f"Total: ${pedido.monto_total}")
print(f"Estado: {pedido.estado_pedido.nombre if pedido.estado_pedido else 'N/A'}")
print(f"\n📦 ITEMS DEL PEDIDO (con lotes asignados):")

for item in pedido.items:
    print(f"\n  Producto: {item.producto.nombre}")
    print(f"  Cantidad: {item.cantidad}")
    print(f"  Precio unitario: ${item.precio_unitario_venta}")
    print(f"  Lote ID: {item.lote_id} ✅" if item.lote_id else "  Lote ID: None ❌")
    
    if item.lote_id:
        lote = db.query(Lote).filter(Lote.id == item.lote_id).first()
        if lote:
            print(f"    → Lote: {lote.codigo_lote}")
            print(f"    → Peso: {lote.peso_actual} kg")
            print(f"    → Vencimiento: {lote.fecha_vencimiento}")
            print(f"    → Vendido: {lote.vendido}")

# Verificar picking items
print(f"\n📋 PICKING ITEMS (peso solicitado):")
if pedido.despacho:
    for picking_item in pedido.despacho.picking_items:
        print(f"\n  Producto: {picking_item.item_pedido.producto.nombre}")
        print(f"  Cantidad solicitada: {picking_item.cantidad_solicitada}")
        print(f"  Peso solicitado: {picking_item.peso_solicitado} kg ✅")
        print(f"  Lote código: {picking_item.lote_codigo}")
        
        if picking_item.peso_solicitado and float(picking_item.peso_solicitado) < 2:
            print(f"  ⚠️  ADVERTENCIA: Peso muy bajo (posible bug)")
        elif picking_item.peso_solicitado and float(picking_item.peso_solicitado) >= 17:
            print(f"  ✅ Peso correcto (rango esperado 17-22 kg)")
else:
    print("  Sin despacho asignado")

db.close()
