"""
Script para recrear el despacho del pedido E-2026-00017 con la nueva lógica
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Pedido, Despacho, PickingItem, EstadoPedido

def recrear_despacho():
    db = SessionLocal()
    try:
        # Buscar el pedido
        pedido = db.query(Pedido).filter(Pedido.numero_pedido == "E-2026-00017").first()
        
        if not pedido:
            print("❌ Pedido E-2026-00017 no encontrado")
            return
        
        print(f"✅ Pedido encontrado: ID={pedido.id}")
        
        # Buscar y eliminar despacho existente
        despacho = db.query(Despacho).filter(Despacho.pedido_id == pedido.id).first()
        
        if despacho:
            print(f"🗑️  Eliminando despacho existente: ID={despacho.id}")
            
            # Eliminar picking items
            picking_items = db.query(PickingItem).filter(PickingItem.despacho_id == despacho.id).all()
            for pi in picking_items:
                db.delete(pi)
            
            # Eliminar despacho
            db.delete(despacho)
            
            # Volver el pedido a CONFIRMADO
            estado_confirmado = db.query(EstadoPedido).filter(EstadoPedido.codigo == "CONFIRMADO").first()
            if estado_confirmado:
                pedido.estado_id = estado_confirmado.id
            
            db.commit()
            print("✅ Despacho eliminado exitosamente")
            print("\n📝 Ahora puedes crear un nuevo despacho desde el backoffice")
            print("   El nuevo despacho usará la lógica actualizada con peso real del lote")
        else:
            print("⚠️ No hay despacho para eliminar")
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    recrear_despacho()
