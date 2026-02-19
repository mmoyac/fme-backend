"""
Script para verificar el pedido E-2026-00017 y su despacho
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session, joinedload
from database.database import SessionLocal
from database.models import Pedido, Despacho, PickingItem, ItemPedido, Lote

def verificar_pedido():
    db = SessionLocal()
    try:
        # Buscar el pedido
        pedido = db.query(Pedido).filter(Pedido.numero_pedido == "E-2026-00017").first()
        
        if not pedido:
            print("❌ Pedido E-2026-00017 no encontrado")
            return
        
        print(f"✅ Pedido encontrado: ID={pedido.id}, Tipo={pedido.tipo_pedido_id}")
        print(f"   Tipo Pedido Código: {pedido.tipo_pedido.codigo if pedido.tipo_pedido else 'N/A'}")
        
        # Buscar items del pedido
        items = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido.id).all()
        print(f"\n📦 Items del pedido ({len(items)}):")
        for item in items:
            print(f"   - Producto: {item.producto.nombre if item.producto else 'N/A'}")
            print(f"     Cantidad: {item.cantidad}")
            print(f"     Lote ID: {item.lote_id}")
            
            if item.lote_id:
                lote = db.query(Lote).filter(Lote.id == item.lote_id).first()
                if lote:
                    print(f"     Lote Código: {lote.codigo_lote}")
                    print(f"     Peso Actual: {lote.peso_actual} kg")
                    print(f"     Fecha Vencimiento: {lote.fecha_vencimiento}")
        
        # Buscar despacho
        despacho = db.query(Despacho).filter(Despacho.pedido_id == pedido.id).first()
        
        if not despacho:
            print("\n⚠️ No hay despacho asignado a este pedido")
            return
        
        print(f"\n🚚 Despacho encontrado: ID={despacho.id}, Estado={despacho.estado_despacho.value}")
        
        # Buscar picking items
        picking_items = db.query(PickingItem).filter(PickingItem.despacho_id == despacho.id).all()
        print(f"\n📋 Picking Items ({len(picking_items)}):")
        for pi in picking_items:
            print(f"   - ID: {pi.id}")
            print(f"     Item Pedido ID: {pi.item_pedido_id}")
            print(f"     Cantidad Solicitada: {pi.cantidad_solicitada}")
            print(f"     Peso Solicitado: {pi.peso_solicitado}")
            print(f"     Lote Código: {pi.lote_codigo}")
            print(f"     Fecha Vencimiento: {pi.fecha_vencimiento}")
            print(f"     Completado: {pi.completado}")
            print()
    
    finally:
        db.close()

if __name__ == "__main__":
    verificar_pedido()
