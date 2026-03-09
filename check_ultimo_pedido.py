from database.database import SessionLocal
from database.models import Pedido, EstadoPedido, ItemPedido, AsignacionPicking, Lote, Producto

db = SessionLocal()

# Ultimo pedido del tenant El Olivo (tenant_id=2)
pedido = (
    db.query(Pedido)
    .join(EstadoPedido, Pedido.estado_id == EstadoPedido.id)
    .filter(Pedido.tenant_id == 2)
    .order_by(Pedido.id.desc())
    .first()
)

if not pedido:
    print("No se encontraron pedidos")
else:
    estado_obj = db.query(EstadoPedido).filter(EstadoPedido.id == pedido.estado_id).first()
    estado = estado_obj.nombre if estado_obj else str(pedido.estado_id)
    print("Pedido #" + str(pedido.id) + " | " + str(getattr(pedido, 'numero_pedido', '-')))
    print("  Estado: " + estado)
    print("  monto_total: " + str(pedido.monto_total))
    print("  inventario_descontado: " + str(pedido.inventario_descontado))
    print("  local_despacho_id: " + str(pedido.local_despacho_id))
    print("  tipo_pedido_id: " + str(pedido.tipo_pedido_id))
    print()
    for item in pedido.items:
        sku = item.producto.sku if item.producto else 'N/A'
        print("  Item " + str(item.id) + " | SKU=" + sku + " | cant=" + str(item.cantidad))
        for asig in item.asignaciones_picking:
            lote_codigo = asig.lote.codigo_lote if asig.lote else 'N/A'
            print("    Asignacion " + str(asig.id) + " | lote=" + lote_codigo + " | peso_real=" + str(asig.peso_real) + "kg | precio_kg=" + str(asig.precio_kg) + " | total=" + str(float(asig.peso_real) * float(asig.precio_kg)))

db.close()
