from database.database import SessionLocal
from database.models import Pedido, Despacho

db = SessionLocal()

p = db.query(Pedido).filter(Pedido.numero_pedido == 'E-2026-00017').first()

if p:
    print(f"Pedido: {p.numero_pedido}")
    print(f"Estado: {p.estado_pedido.codigo}")
    if p.local_despacho:
        print(f"Local despacho: {p.local_despacho.nombre}")
    else:
        print("Local despacho: No asignado")
    
    # Verificar si ya tiene despacho asignado
    despacho = db.query(Despacho).filter(Despacho.pedido_id == p.id).first()
    if despacho:
        print(f"\nDespacho existente:")
        print(f"  ID: {despacho.id}")
        print(f"  Estado: {despacho.estado}")
        if despacho.despachador:
            print(f"  Despachador: {despacho.despachador.nombre_completo}")
    else:
        print("\nDespacho: No asignado")

db.close()
