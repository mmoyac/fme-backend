from database.database import SessionLocal
from database.models import Pedido, Cliente, Despacho, EstadoPedido

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00030'
).first()

if not pedido:
    print("❌ Pedido no encontrado")
    exit()

estado = db.query(EstadoPedido).filter(EstadoPedido.id == pedido.estado_id).first()

print(f"=== ESTADO FINAL PEDIDO {pedido.numero_pedido} ===\n")
print(f"Estado del Pedido: {estado.nombre} (codigo: {estado.codigo})")
print(f"Total: ${pedido.monto_total}")
print(f"Pagado: {'SI' if pedido.es_pagado else 'NO'}")
print(f"Inventario descontado: {'SI' if pedido.inventario_descontado else 'NO'}")

print(f"\n🚚 ESTADO DEL DESPACHO:")
if pedido.despacho:
    despacho = pedido.despacho
    print(f"  ID: {despacho.id}")
    print(f"  Estado: {despacho.estado_despacho}")
    print(f"  Fecha asignación: {despacho.fecha_asignacion}")
    print(f"  Fecha inicio picking: {despacho.fecha_inicio_picking}")
    print(f"  Fecha fin picking: {despacho.fecha_fin_picking}")
    print(f"  Fecha inicio ruta: {despacho.fecha_inicio_ruta}")
    print(f"  Fecha entrega: {despacho.fecha_entrega}")
    
    print(f"\n📋 PICKING ITEMS COMPLETADOS:")
    items_completados = sum(1 for pi in despacho.picking_items if pi.completado)
    print(f"  {items_completados}/{len(despacho.picking_items)} items completados")
    
    for idx, picking_item in enumerate(despacho.picking_items, 1):
        estado_item = "✅" if picking_item.completado else "⏳"
        print(f"  {estado_item} [{idx}] {picking_item.lote_codigo} - {picking_item.peso_real} kg")
else:
    print("  Sin despacho asignado")

print(f"\n🔍 FLUJO COMPLETO:")
print(f"  ✅ Pedido creado → {estado.codigo}")
print(f"  ✅ Pedido confirmado → CONFIRMADO")
print(f"  ✅ Despacho asignado → EN_PREPARACION")
print(f"  ✅ Picking completado → LISTO_EMPAQUE")
print(f"  ✅ En ruta → EN_RUTA")
print(f"  ✅ Entregado → Despacho: ENTREGADO")
print(f"  {'✅' if estado.codigo == 'ENTREGADO' else '❌'} Estado final pedido: {estado.codigo}")

if estado.codigo != 'ENTREGADO':
    print(f"\n⚠️  ADVERTENCIA: El estado del pedido NO se actualizó a ENTREGADO")
    print(f"   El despacho está en estado ENTREGADO pero el pedido sigue en: {estado.codigo}")
    print(f"   Esto puede indicar que falta sincronización entre despacho y pedido")

db.close()
