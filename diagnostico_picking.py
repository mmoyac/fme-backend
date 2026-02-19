from database.database import SessionLocal
from database.models import Pedido, ItemPedido, Lote, Cliente, PickingItem, Despacho

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00029'
).first()

if not pedido:
    print("❌ Pedido no encontrado")
    exit()

print(f"=== DIAGNOSTICO PEDIDO {pedido.numero_pedido} ===\n")
print(f"Estado: {pedido.estado_pedido.nombre if pedido.estado_pedido else 'N/A'}")
print(f"Total: ${pedido.monto_total}")
print(f"Tipo: {pedido.tipo_pedido.nombre if pedido.tipo_pedido else 'N/A'} (codigo: {pedido.tipo_pedido.codigo if pedido.tipo_pedido else 'N/A'})")

print(f"\n📦 ITEMS DEL PEDIDO:")
print(f"Total items: {len(pedido.items)}")

for idx, item in enumerate(pedido.items, 1):
    print(f"\n  [{idx}] {item.producto.nombre}")
    print(f"      Cantidad: {item.cantidad}")
    print(f"      Precio unitario: ${item.precio_unitario_venta}")
    print(f"      Lote ID: {item.lote_id}")
    
    if item.lote_id:
        lote = db.query(Lote).filter(Lote.id == item.lote_id).first()
        if lote:
            print(f"      → Lote: {lote.codigo_lote}")
            print(f"      → Peso: {lote.peso_actual} kg")

print(f"\n🚚 DESPACHO:")
if pedido.despacho:
    despacho = pedido.despacho
    print(f"  ID: {despacho.id}")
    print(f"  Estado: {despacho.estado_despacho}")
    print(f"  Picking items: {len(despacho.picking_items)}")
    
    print(f"\n📋 PICKING ITEMS:")
    for idx, picking_item in enumerate(despacho.picking_items, 1):
        print(f"\n  [{idx}] {picking_item.item_pedido.producto.nombre}")
        print(f"      Item Pedido ID: {picking_item.item_pedido_id}")
        print(f"      Cantidad solicitada: {picking_item.cantidad_solicitada}")
        print(f"      Peso solicitado: {picking_item.peso_solicitado} kg")
        print(f"      Lote código: {picking_item.lote_codigo}")
        print(f"      Completado: {picking_item.completado}")
else:
    print("  ⚠️  Sin despacho asignado")

print(f"\n🔍 ANALISIS:")
if len(pedido.items) != len(pedido.despacho.picking_items if pedido.despacho else []):
    print(f"  ❌ PROBLEMA: El pedido tiene {len(pedido.items)} items pero el despacho tiene {len(pedido.despacho.picking_items if pedido.despacho else 0)} picking items")
    print(f"  ⚠️  Falta crear picking items para algunos productos")
else:
    print(f"  ✅ Cantidad correcta: {len(pedido.items)} items = {len(pedido.despacho.picking_items if pedido.despacho else 0)} picking items")

db.close()
