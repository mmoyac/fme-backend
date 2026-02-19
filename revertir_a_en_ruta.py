"""Revertir despacho 48 a EN_RUTA para prueba manual."""
from database.database import SessionLocal
from database.models import Despacho, Pedido, EstadoPedido, EstadoDespacho

db = SessionLocal()

print("=" * 60)
print("🔄 REVIRTIENDO DESPACHO 48 PARA PRUEBA MANUAL")
print("=" * 60)

# Obtener despacho y pedido
despacho = db.query(Despacho).filter(Despacho.id == 48).first()
if not despacho:
    print("❌ Despacho 48 no encontrado")
    db.close()
    exit()

pedido = despacho.pedido

# Obtener estados
estado_prep = db.query(EstadoPedido).filter(
    EstadoPedido.codigo == 'EN_PREPARACION'
).first()

print(f"\n📊 ESTADO ACTUAL:")
print(f"   Despacho: {despacho.estado_despacho}")
print(f"   Pedido: {pedido.estado_id}")

print(f"\n🔄 REVIRTIENDO...")
print(f"   Despacho 48 → EN_RUTA")
print(f"   Pedido E-2026-00032 → EN_PREPARACION")

# Revertir estados
despacho.estado_despacho = EstadoDespacho.EN_RUTA
despacho.fecha_entrega = None  # Limpiar fecha de entrega
pedido.estado_id = estado_prep.id

db.commit()

print(f"\n✅ REVERTIDO EXITOSAMENTE")
print(f"\n📋 AHORA PUEDES:")
print(f"   1. Ir a: http://elolivo.local:3001/admin/despacho/48")
print(f"   2. Cambiar estado a ENTREGADO desde el backoffice")
print(f"   3. Verificar que el pedido E-2026-00032 cambie a ENTREGADO")

print("=" * 60)

db.close()
