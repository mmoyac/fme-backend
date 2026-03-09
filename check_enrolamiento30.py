from database.database import SessionLocal
from database.models import Enrolamiento, Lote, Producto

db = SessionLocal()
enr = db.query(Enrolamiento).filter(Enrolamiento.id == 30).first()

if not enr:
    print("Enrolamiento #30 no encontrado")
else:
    estado = enr.estado.codigo if enr.estado else 'N/A'
    proveedor = enr.proveedor.nombre if enr.proveedor else 'N/A'
    print("Enrolamiento #" + str(enr.id))
    print("  Estado: " + estado)
    print("  Proveedor: " + proveedor)
    print("  Fecha: " + str(getattr(enr, 'fecha_enrolamiento', getattr(enr, 'fecha_llegada', getattr(enr, 'fecha_creacion', 'N/A')))))
    print("  Total lotes: " + str(len(enr.lotes)))
    print("")
    for lote in enr.lotes:
        sku = lote.producto.sku if lote.producto else 'N/A'
        print("  Lote " + str(lote.id) + " | SKU=" + sku + " | QR=" + str(lote.qr_original) + " | Peso=" + str(lote.peso_actual) + "kg | Venc=" + str(lote.fecha_vencimiento) + " | disponible=" + str(lote.disponible_venta) + " | vendido=" + str(lote.vendido))

db.close()
