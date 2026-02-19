"""
Script para verificar el nuevo flujo optimizado:
EN_PICKING → Completar Picking → EN_RUTA (automático)
"""
from database.database import SessionLocal
from database.models import Despacho, Cliente, Pedido

db = SessionLocal()

# Buscar el último despacho de El Olivo
despacho = db.query(Despacho).join(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2
).order_by(Despacho.id.desc()).first()

if not despacho:
    print("❌ No hay despachos para verificar")
    db.close()
    exit()

print("=" * 60)
print("🚀 VERIFICACIÓN DE FLUJO OPTIMIZADO")
print("=" * 60)
print(f"\n📦 Despacho ID: {despacho.id}")
print(f"📋 Pedido: {despacho.pedido.numero_pedido}")
print(f"🏢 Cliente: {despacho.pedido.cliente.nombre}")

print(f"\n📊 ESTADO ACTUAL:")
print(f"   Despacho: {despacho.estado_despacho}")

print(f"\n⏱️  TIMESTAMPS:")
print(f"   Asignación: {despacho.fecha_asignacion}")
print(f"   Inicio picking: {despacho.fecha_inicio_picking}")
print(f"   Fin picking: {despacho.fecha_fin_picking}")
print(f"   Inicio ruta: {despacho.fecha_inicio_ruta}")
print(f"   Entrega: {despacho.fecha_entrega}")

# Verificar picking items
picking_items = despacho.picking_items
total_items = len(picking_items)
completados = sum(1 for item in picking_items if item.completado)

print(f"\n📦 PICKING ITEMS: {completados}/{total_items} completados")
for idx, item in enumerate(picking_items, 1):
    status = "✅" if item.completado else "⏳"
    peso = item.peso_real or item.peso_solicitado
    print(f"   {status} [{idx}] {item.lote_codigo} - {peso} kg")

print("\n" + "=" * 60)

# Validar el flujo optimizado
if despacho.estado_despacho.value == "EN_RUTA":
    if despacho.fecha_fin_picking and despacho.fecha_inicio_ruta:
        tiempo_transicion = (despacho.fecha_inicio_ruta - despacho.fecha_fin_picking).total_seconds()
        print("✅ FLUJO OPTIMIZADO FUNCIONANDO CORRECTAMENTE")
        print(f"   Transición automática en {tiempo_transicion:.2f} segundos")
        print(f"   EN_PICKING → Completar → EN_RUTA ✅")
    else:
        print("⚠️  Estado EN_RUTA pero faltan timestamps")
elif despacho.estado_despacho.value == "LISTO_EMPAQUE":
    print("⚠️  FLUJO ANTIGUO DETECTADO")
    print("   Aún usa estado LISTO_EMPAQUE (requiere actualización)")
elif despacho.estado_despacho.value == "EN_PICKING":
    print("⏳ Picking aún en proceso")
elif despacho.estado_despacho.value == "ENTREGADO":
    print("✅ Despacho completado exitosamente")
else:
    print(f"📌 Estado actual: {despacho.estado_despacho.value}")

print("=" * 60)

db.close()
