from database.database import SessionLocal
from database.models import Pedido, MovimientoStockCajas, Lote, StockCajasProveedor

db = SessionLocal()

# Verificar pedido
p = db.query(Pedido).filter(Pedido.id == 78).first()
print("=== PEDIDO #78 ===")
print(f"Estado: {p.estado_pedido.codigo}")
print(f"inventario_descontado: {p.inventario_descontado}")
print(f"Items: {len(p.items)}")

# Verificar movimientos
movs = db.query(MovimientoStockCajas).filter(
    MovimientoStockCajas.referencia_id == 78,
    MovimientoStockCajas.referencia_tipo == 'PEDIDO'
).all()

print(f"\n=== MOVIMIENTOS ({len(movs)}) ===")
for m in movs:
    print(f"ID: {m.id}, Tipo: {m.tipo_movimiento}, Lote: {m.lote_codigo}")

# Verificar lotes
if movs:
    lote_codigo = movs[0].lote_codigo
    lote = db.query(Lote).filter(Lote.codigo_lote == lote_codigo).first()
    if lote:
        print(f"\n=== LOTE {lote_codigo} ===")
        print(f"disponible_venta: {lote.disponible_venta}")
        print(f"vendido: {lote.vendido}")
        
        # Verificar stock
        stock = db.query(StockCajasProveedor).filter(
            StockCajasProveedor.proveedor_id == lote.proveedor_id,
            StockCajasProveedor.producto_id == lote.producto_id,
            StockCajasProveedor.local_id == lote.local_id
        ).first()
        
        if stock:
            print(f"\n=== STOCK ===")
            print(f"cajas_disponibles: {stock.cajas_disponibles}")
            print(f"cajas_totales_vendidas: {stock.cajas_totales_vendidas}")
    else:
        print(f"\n❌ No se encontró el lote {lote_codigo}")

db.close()
