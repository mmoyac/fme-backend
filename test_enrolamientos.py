from database.database import SessionLocal
from database.models import Enrolamiento, Lote, Producto, Proveedor
from sqlalchemy.orm import joinedload

db = SessionLocal()

print('=== ENROLAMIENTOS DISPONIBLES ===')
enrolamientos = db.query(Enrolamiento).options(joinedload(Enrolamiento.proveedor)).all()

for e in enrolamientos:
    proveedor_nombre = e.proveedor.nombre if e.proveedor else 'Sin proveedor'
    print('ID:', e.id, '| Estado:', e.estado, '| Proveedor:', proveedor_nombre, '| Fecha:', e.fecha_enrolamiento)
    
    lotes = db.query(Lote).filter(Lote.enrolamiento_id == e.id).all()
    for lote in lotes:
        producto = db.query(Producto).filter(Producto.id == lote.producto_id).first()
        producto_nombre = producto.nombre if producto else 'Producto desconocido'
        categoria = producto.categoria if producto else 'N/A'
        print('  -', lote.cantidad_total, 'cajas de', producto_nombre, '(Categoria:', categoria, ')')

print('\n=== STOCK ACTUAL DE CAJAS ===')
from database.models import StockCajasProveedor

stock_items = db.query(StockCajasProveedor).all()
for stock in stock_items:
    producto = db.query(Producto).filter(Producto.id == stock.producto_id).first()
    proveedor = db.query(Proveedor).filter(Proveedor.id == stock.proveedor_id).first()
    print('Proveedor:', proveedor.nombre if proveedor else 'N/A', 
          '| Producto:', producto.nombre if producto else 'N/A', 
          '| Stock:', stock.cantidad_disponible)

db.close()