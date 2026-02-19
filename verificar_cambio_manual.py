"""Verificar estado final después de cambio manual desde backoffice."""
from database.database import SessionLocal
from database.models import Despacho, Pedido, EstadoPedido

db = SessionLocal()

print("=" * 60)
print("🔍 VERIFICACIÓN DESPUÉS DE CAMBIO MANUAL")
print("=" * 60)

# Verificar despacho 48
despacho = db.query(Despacho).filter(Despacho.id == 48).first()
if not despacho:
    print("❌ Despacho 48 no encontrado")
    db.close()
    exit()

pedido = despacho.pedido
estado_pedido = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"\n📦 DESPACHO #48:")
print(f"   Estado: {despacho.estado_despacho}")
print(f"   Fecha entrega: {despacho.fecha_entrega}")
print(f"   Fecha inicio ruta: {despacho.fecha_inicio_ruta}")

print(f"\n📋 PEDIDO #{pedido.id} ({pedido.numero_pedido}):")
print(f"   Cliente: {pedido.cliente.nombre}")
print(f"   Estado ID: {pedido.estado_id}")
print(f"   Estado: {estado_pedido.nombre}")
print(f"   Código: {estado_pedido.codigo}")

print("\n" + "=" * 60)

# Validar sincronización
if despacho.estado_despacho.value == "ENTREGADO":
    if estado_pedido.codigo == "ENTREGADO":
        print("✅✅✅ ÉXITO TOTAL ✅✅✅")
        print("\n🎉 LA ACTUALIZACIÓN MANUAL FUNCIONÓ CORRECTAMENTE")
        print(f"   Despacho #48: ENTREGADO ✅")
        print(f"   Pedido #{pedido.id}: ENTREGADO ✅")
        print(f"   Sincronización: PERFECTA ✅")
    else:
        print("❌ FALLO EN SINCRONIZACIÓN")
        print(f"   Despacho: ENTREGADO")
        print(f"   Pedido: {estado_pedido.codigo} (debería ser ENTREGADO)")
else:
    print(f"⚠️ Despacho no está en ENTREGADO: {despacho.estado_despacho.value}")

print("=" * 60)

db.close()
