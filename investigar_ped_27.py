#!/usr/bin/env python3
"""
Script para investigar y corregir el pedido PED-00027
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido, ItemPedido, Producto
from services.puntos_service import PuntosService

def investigar_ped_27():
    db = SessionLocal()
    
    try:
        print("🔍 INVESTIGANDO PEDIDO PED-00027")
        print("=" * 50)
        
        # Obtener el pedido 27
        pedido = db.query(Pedido).filter(Pedido.id == 27).first()
        if not pedido:
            print("❌ No se encontró el pedido 27")
            return
        
        print(f"📦 PEDIDO 27:")
        print(f"   Estado: {pedido.estado}")
        print(f"   Cliente ID: {pedido.cliente_id}")
        print(f"   Total: ${pedido.monto_total:,.0f}")
        print(f"   Puntos ganados: {pedido.puntos_ganados}")
        print(f"   Puntos usados: {pedido.puntos_usados}")
        print(f"   Descuento por puntos: ${pedido.descuento_puntos}")
        
        # Obtener los items del pedido
        print(f"\n📝 ITEMS DEL PEDIDO:")
        items = db.query(ItemPedido).filter(ItemPedido.pedido_id == 27).all()
        
        for item in items:
            producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
            print(f"   - {producto.nombre if producto else 'Producto no encontrado'}")
            print(f"     Cantidad: {item.cantidad}")
            print(f"     Precio unitario: ${item.precio_unitario_venta:,.0f}")
            subtotal = item.precio_unitario_venta * item.cantidad
            print(f"     Subtotal: ${subtotal:,.0f}")
            if producto and producto.categoria:
                print(f"     Categoría: {producto.categoria.nombre}")
                print(f"     Puntos por unidad: {producto.categoria.puntos_fidelidad}")
                expected_points = producto.categoria.puntos_fidelidad * item.cantidad
                print(f"     Puntos esperados: {expected_points}")
        
        # Calcular puntos que debería tener manualmente
        print(f"\n🧮 CÁLCULO DE PUNTOS:")
        total_puntos_esperados = 0
        for item in items:
            producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
            if producto and producto.categoria:
                puntos_item = producto.categoria.puntos_fidelidad * item.cantidad
                total_puntos_esperados += puntos_item
        
        print(f"   Puntos en BD: {pedido.puntos_ganados}")
        print(f"   Puntos esperados: {total_puntos_esperados}")
        print(f"   ¿Debería actualizar? {'✅ SÍ' if total_puntos_esperados != pedido.puntos_ganados else '❌ NO'}")
        
        # Si el pedido está pendiente, no debería haber usado puntos
        if pedido.estado == 'PENDIENTE' and pedido.puntos_usados > 0:
            print(f"\n⚠️  PROBLEMA: Pedido PENDIENTE no debería tener puntos usados")
            print(f"   Puntos usados incorrectamente: {pedido.puntos_usados}")
        
        # Corregir si es necesario
        respuesta = input("\n🔧 ¿Quieres corregir los puntos ganados del pedido? (s/n): ")
        if respuesta.lower() == 's':
            pedido.puntos_ganados = total_puntos_esperados
            db.commit()
            print(f"✅ Puntos ganados actualizados a {total_puntos_esperados}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    investigar_ped_27()