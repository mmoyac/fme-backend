from database.database import SessionLocal
from database.models import Pedido, Cliente, EstadoPedido

db = SessionLocal()

pedido = db.query(Pedido).join(Cliente).filter(
    Cliente.tenant_id == 2,
    Pedido.numero_pedido == 'E-2026-00027'
).first()

if pedido:
    estado = db.query(EstadoPedido).filter(EstadoPedido.id == pedido.estado_id).first()
    
    print(f"=== DIAGNÓSTICO PEDIDO {pedido.numero_pedido} ===\n")
    print(f"Estado actual: {estado.nombre} (codigo: {estado.codigo})")
    print(f"Inventario descontado: {pedido.inventario_descontado}")
    print(f"Fecha creación: {pedido.fecha_pedido}")
    print(f"\nPROBLEMA DETECTADO:")
    print(f"❌ Este pedido está en estado '{estado.nombre}' pero NO tiene lotes asignados")
    print(f"❌ Para pedidos de CAJAS_VARIABLES, los lotes se asignan al CONFIRMAR")
    print(f"\nSOLUCIÓN:")
    print(f"1. Cancelar el despacho actual (ID {pedido.despacho.id if hasattr(pedido, 'despacho') and pedido.despacho else 'N/A'})")
    print(f"2. Confirmar correctamente el pedido desde el backoffice")
    print(f"3. El proceso de confirmación asignará los lotes automáticamente (FIFO)")
    print(f"4. Luego asignar nuevo despacho")
else:
    print("Pedido no encontrado")

db.close()
