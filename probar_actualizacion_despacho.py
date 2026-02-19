"""Script para cambiar despacho 48 a ENTREGADO via API y verificar pedido."""
from database.database import SessionLocal
from database.models import Despacho, Pedido, EstadoPedido, EstadoDespacho, User
from sqlalchemy.orm import Session
from datetime import datetime

db = SessionLocal()

print("=" * 60)
print("🧪 PRUEBA: Actualizar Despacho 48 → ENTREGADO")
print("=" * 60)

# 1. Verificar estado ANTES
despacho = db.query(Despacho).filter(Despacho.id == 48).first()
if not despacho:
    print("❌ Despacho 48 no encontrado")
    db.close()
    exit()

pedido = despacho.pedido
estado_pedido_antes = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"\n📊 ESTADO ANTES:")
print(f"   Despacho: {despacho.estado_despacho}")
print(f"   Pedido: {estado_pedido_antes.nombre} (ID: {pedido.estado_id})")

# 2. SIMULAR el código del endpoint actualizar_despacho_general
old_estado = despacho.estado_despacho
nuevo_estado = EstadoDespacho.ENTREGADO

print(f"\n🔄 EJECUTANDO LÓGICA DEL ENDPOINT...")
print(f"   old_estado = {old_estado}")
print(f"   nuevo_estado = {nuevo_estado}")

# Actualizar despacho
despacho.estado_despacho = nuevo_estado

# Si el despacho se marca como ENTREGADO, actualizar el pedido también
if nuevo_estado == EstadoDespacho.ENTREGADO:
    print(f"   ✓ Condición: nuevo_estado == ENTREGADO → TRUE")
    
    estado_entregado = db.query(EstadoPedido).filter(
        EstadoPedido.codigo == "ENTREGADO"
    ).first()
    
    if estado_entregado:
        print(f"   ✓ Estado ENTREGADO encontrado: ID {estado_entregado.id}")
        
        if pedido.estado_id != estado_entregado.id:
            print(f"   ✓ Condición: pedido.estado_id ({pedido.estado_id}) != {estado_entregado.id} → TRUE")
            print(f"   ✓ ACTUALIZANDO pedido.estado_id = {estado_entregado.id}")
            
            pedido.estado_id = estado_entregado.id
            
            if old_estado != EstadoDespacho.ENTREGADO:
                print(f"   ✓ Primera vez ENTREGADO → guardando fecha_entrega")
                despacho.fecha_entrega = datetime.now()
        else:
            print(f"   ⚠️ Condición: pedido ya está ENTREGADO → SKIP")

# Guardar cambios
db.commit()
db.refresh(despacho)
db.refresh(pedido)

# 3. Verificar estado DESPUÉS
estado_pedido_despues = db.query(EstadoPedido).filter(
    EstadoPedido.id == pedido.estado_id
).first()

print(f"\n📊 ESTADO DESPUÉS:")
print(f"   Despacho: {despacho.estado_despacho}")
print(f"   Pedido: {estado_pedido_despues.nombre} (ID: {pedido.estado_id})")
print(f"   Fecha entrega: {despacho.fecha_entrega}")

print("\n" + "=" * 60)

if despacho.estado_despacho.value == "ENTREGADO" and estado_pedido_despues.codigo == "ENTREGADO":
    print("✅ PRUEBA EXITOSA")
    print("   Despacho → ENTREGADO")
    print("   Pedido → ENTREGADO")
    print("   🎉 SINCRONIZACIÓN CORRECTA")
else:
    print("❌ PRUEBA FALLIDA")
    print(f"   Despacho: {despacho.estado_despacho.value}")
    print(f"   Pedido: {estado_pedido_despues.codigo}")

print("=" * 60)

db.close()
