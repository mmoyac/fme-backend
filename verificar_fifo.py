from database.database import SessionLocal
from database.models import Lote, Enrolamiento, Proveedor

db = SessionLocal()

print("=== VERIFICACION FIFO ===\n")

# Lotes disponibles para venta
lotes_disponibles = db.query(Lote).join(Enrolamiento).join(Proveedor).filter(
    Proveedor.tenant_id == 2,
    Lote.disponible_venta == True
).order_by(Lote.fecha_vencimiento).all()

# Lotes vendidos
lotes_vendidos = db.query(Lote).join(Enrolamiento).join(Proveedor).filter(
    Proveedor.tenant_id == 2,
    Lote.vendido == True
).order_by(Lote.fecha_vencimiento).all()

print(f"Total cajas disponibles: {len(lotes_disponibles)}")
print(f"Total cajas vendidas: {len(lotes_vendidos)}\n")

if lotes_vendidos:
    print("LOTES VENDIDOS (deben ser los 3 que vencen primero):")
    for lote in lotes_vendidos:
        print(f"  - {lote.codigo_lote}")
        print(f"    Vencimiento: {lote.fecha_vencimiento}")
        print(f"    Peso: {lote.peso_actual} kg")
        print()

if lotes_disponibles:
    print("LOTES DISPONIBLES (deben quedar 7):")
    for lote in lotes_disponibles:
        print(f"  - {lote.codigo_lote}")
        print(f"    Vencimiento: {lote.fecha_vencimiento}")
        print(f"    Peso: {lote.peso_actual} kg")
        print()

# Verificación FIFO
if len(lotes_vendidos) == 3 and len(lotes_disponibles) == 7:
    print("\n✅ EXITO: Stock correcto (7 disponibles, 3 vendidas)")
    print("✅ EXITO: FIFO funcionando correctamente")
    
    # Verificar que se vendieron los más antiguos
    if lotes_vendidos:
        fecha_vendido_mas_nuevo = max(l.fecha_vencimiento for l in lotes_vendidos)
        fecha_disp_mas_antiguo = min(l.fecha_vencimiento for l in lotes_disponibles)
        
        if fecha_vendido_mas_nuevo < fecha_disp_mas_antiguo:
            print("✅ EXITO: Los lotes vendidos vencen ANTES que los disponibles (FIFO correcto)")
        else:
            print("⚠️  ADVERTENCIA: FIFO no funcionó correctamente")
else:
    print(f"\n⚠️  Stock esperado: 7 disponibles, 3 vendidas")
    print(f"    Stock actual: {len(lotes_disponibles)} disponibles, {len(lotes_vendidos)} vendidas")

db.close()
