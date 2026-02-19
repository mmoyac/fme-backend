from database.database import SessionLocal
from database.models import Pedido, Lote, MovimientoStockCajas, StockCajasProveedor

db = SessionLocal()

# Obtener pedido #78
pedido_id = 78
p = db.query(Pedido).filter(Pedido.id == pedido_id).first()

if not p:
    print(f"❌ Pedido #{pedido_id} no encontrado")
    db.close()
    exit(1)

print(f"=== LIBERANDO LOTES DEL PEDIDO #{pedido_id} ===")
print(f"Estado: {p.estado_pedido.codigo}")

# Buscar movimientos de RESERVA_LOTE
movimientos_reserva = db.query(MovimientoStockCajas).filter(
    MovimientoStockCajas.referencia_tipo == "PEDIDO",
    MovimientoStockCajas.referencia_id == pedido_id,
    MovimientoStockCajas.tipo_movimiento == "RESERVA_LOTE"
).all()

print(f"Movimientos de RESERVA encontrados: {len(movimientos_reserva)}")

for movimiento in movimientos_reserva:
    if movimiento.lote_codigo:
        # Buscar el lote
        lote = db.query(Lote).filter(
            Lote.codigo_lote == movimiento.lote_codigo
        ).first()
        
        if lote:
            print(f"\n📦 Procesando lote: {lote.codigo_lote}")
            print(f"   Estado actual: disponible_venta={lote.disponible_venta}, vendido={lote.vendido}")
            
            # Restaurar lote al estado disponible
            lote.vendido = False
            lote.disponible_venta = True
            
            # Restaurar stock de cajas
            stock_cajas = db.query(StockCajasProveedor).filter(
                StockCajasProveedor.producto_id == movimiento.producto_id,
                StockCajasProveedor.proveedor_id == movimiento.proveedor_id
            ).first()
            
            if stock_cajas:
                stock_anterior = stock_cajas.cajas_disponibles
                stock_cajas.cajas_disponibles += 1
                print(f"   Stock: {stock_anterior} → {stock_cajas.cajas_disponibles} cajas disponibles")
            
            # Registrar movimiento de liberación
            movimiento_liberacion = MovimientoStockCajas(
                producto_id=movimiento.producto_id,
                proveedor_id=movimiento.proveedor_id,
                tipo_movimiento="LIBERACION_RESERVA",
                cajas_movimiento=1,
                peso_total_kg=movimiento.peso_total_kg,
                descripcion=f"Liberación lote {movimiento.lote_codigo} por corrección manual del pedido #{pedido_id}",
                referencia_tipo="PEDIDO",
                referencia_id=pedido_id,
                lote_codigo=movimiento.lote_codigo,
                usuario="sistema"
            )
            db.add(movimiento_liberacion)
            
            print(f"   ✅ Lote liberado y stock restaurado")
        else:
            print(f"   ❌ Lote {movimiento.lote_codigo} no encontrado")

# Confirmar cambios
db.commit()
print(f"\n✅ COMPLETADO: Lotes liberados y stock restaurado para pedido #{pedido_id}")

db.close()
