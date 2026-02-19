"""Verificar estado del despacho 48 y su pedido asociado."""
from database.database import SessionLocal
from database.models import Despacho, Pedido, EstadoPedido

db = SessionLocal()

despacho = db.query(Despacho).filter(Despacho.id == 48).first()

if not despacho:
    print("❌ Despacho 48 no encontrado")
    db.close()
    exit()

pedido = despacho.pedido
estado_pedido = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print("=" * 60)
print(f"🔍 VERIFICACIÓN DESPACHO ID: {despacho.id}")
print("=" * 60)
print(f"\n📦 DESPACHO:")
print(f"   Estado: {despacho.estado_despacho}")
print(f"   Fecha entrega: {despacho.fecha_entrega}")
print(f"   Fecha inicio ruta: {despacho.fecha_inicio_ruta}")

print(f"\n📋 PEDIDO:")
print(f"   Número: {pedido.numero_pedido}")
print(f"   Estado ID: {pedido.estado_id}")
print(f"   Estado: {estado_pedido.nombre} (codigo: {estado_pedido.codigo})")
print(f"   Inventario descontado: {'SÍ' if pedido.inventario_descontado else 'NO'}")

print("\n" + "=" * 60)

if despacho.estado_despacho.value == "ENTREGADO":
    if estado_pedido.codigo == "ENTREGADO":
        print("✅ SINCRONIZACIÓN CORRECTA")
        print("   Despacho ENTREGADO → Pedido ENTREGADO")
    else:
        print("❌ DESINCRONIZACIÓN DETECTADA")
        print(f"   Despacho: ENTREGADO")
        print(f"   Pedido: {estado_pedido.codigo} (debería ser ENTREGADO)")
        print("\n🔧 CORRIGIENDO...")
        
        estado_entregado = db.query(EstadoPedido).filter(
            EstadoPedido.codigo == "ENTREGADO"
        ).first()
        
        if estado_entregado:
            pedido.estado_id = estado_entregado.id
            db.commit()
            print("✅ Pedido corregido a ENTREGADO")
else:
    print(f"📌 Estado actual del despacho: {despacho.estado_despacho.value}")

print("=" * 60)

db.close()
