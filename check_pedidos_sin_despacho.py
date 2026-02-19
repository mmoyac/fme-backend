from database.database import SessionLocal
from database.models import Pedido, Despacho, EstadoPedido

db = SessionLocal()

# Buscar pedidos CONFIRMADOS sin despacho asignado
estado_confirmado = db.query(EstadoPedido).filter(EstadoPedido.codigo == 'CONFIRMADO').first()

if estado_confirmado:
    pedidos_confirmados = db.query(Pedido).filter(
        Pedido.estado_id == estado_confirmado.id,
        Pedido.tenant_id == 2  # El Olivo
    ).all()
    
    print("=" * 80)
    print("📦 PEDIDOS CONFIRMADOS (Tenant: El Olivo)")
    print("=" * 80)
    print(f"Total: {len(pedidos_confirmados)}\n")
    
    pendientes_asignar = []
    
    for p in pedidos_confirmados:
        # Verificar si tiene despacho asignado
        despacho = db.query(Despacho).filter(Despacho.pedido_id == p.id).first()
        
        tiene_despacho = "✅ ASIGNADO" if despacho else "⚠️  SIN ASIGNAR"
        
        if not despacho:
            pendientes_asignar.append(p)
        
        print(f"Pedido: {p.numero_pedido}")
        print(f"  Cliente: {p.cliente.nombre}")
        print(f"  Local despacho: {p.local_despacho.nombre if p.local_despacho else 'N/A'}")
        print(f"  Total: ${p.monto_total:,.0f}")
        print(f"  Estado despacho: {tiene_despacho}")
        
        if despacho:
            print(f"    - ID despacho: {despacho.id}")
            print(f"    - Estado: {despacho.estado}")
            if despacho.despachador:
                print(f"    - Despachador: {despacho.despachador.nombre_completo}")
        print()
    
    print("=" * 80)
    print(f"🚨 PEDIDOS PENDIENTES DE ASIGNAR: {len(pendientes_asignar)}")
    print("=" * 80)
    
    if pendientes_asignar:
        print("\n⚠️  REQUIEREN ATENCIÓN INMEDIATA:")
        for p in pendientes_asignar:
            print(f"  • {p.numero_pedido} - {p.cliente.nombre} - ${p.monto_total:,.0f}")
    else:
        print("\n✅ Todos los pedidos confirmados tienen despacho asignado")

else:
    print("❌ Estado CONFIRMADO no encontrado")

db.close()
