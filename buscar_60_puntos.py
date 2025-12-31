#!/usr/bin/env python3
"""
Script para buscar cualquier pedido que tenga exactamente 60 puntos ganados.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido, ItemPedido, Producto, CategoriaProducto, Cliente
from services.puntos_service import PuntosService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def buscar_pedido_60_puntos():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔍 BÚSQUEDA: Pedidos con 60 puntos ===")
        
        # 1. Buscar pedidos con puntos_ganados = 60
        pedidos_60 = db.query(Pedido).filter(Pedido.puntos_ganados == 60).all()
        
        print(f"📊 Pedidos con exactamente 60 puntos_ganados: {len(pedidos_60)}")
        
        if not pedidos_60:
            print("❌ No se encontraron pedidos con 60 puntos ganados")
            
            # Mostrar todos los pedidos con puntos ganados
            todos_con_puntos = db.query(Pedido).filter(Pedido.puntos_ganados > 0).all()
            print(f"\n📋 Todos los pedidos con puntos ganados ({len(todos_con_puntos)}):")
            
            for pedido in todos_con_puntos:
                cliente = pedido.cliente
                print(f"   Pedido #{pedido.id}: {pedido.puntos_ganados} puntos - Cliente: {cliente.nombre}")
                print(f"     Estado: {pedido.estado}, Total: ${pedido.monto_total}, Fecha: {pedido.fecha_pedido}")
                
                # Mostrar items
                items = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido.id).all()
                for item in items:
                    producto = item.producto
                    categoria = producto.categoria
                    print(f"       - {producto.nombre} x{item.cantidad} (Categoría: {categoria.nombre if categoria else 'Sin categoría'})")
            
            return
        
        # 2. Analizar cada pedido con 60 puntos
        for pedido in pedidos_60:
            cliente = pedido.cliente
            print(f"\n🎯 PEDIDO CON 60 PUNTOS:")
            print(f"   ID: {pedido.id}")
            print(f"   Cliente: {cliente.nombre} - {cliente.email}")
            print(f"   Estado: {pedido.estado}")
            print(f"   Total: ${pedido.monto_total}")
            print(f"   Puntos ganados: {pedido.puntos_ganados}")
            print(f"   Fecha: {pedido.fecha_pedido}")
            
            # Ver items del pedido
            items = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido.id).all()
            print(f"   Items en el pedido:")
            
            puntos_calculados_manual = 0
            for item in items:
                producto = item.producto
                categoria = producto.categoria
                
                puntos_item = 0
                if categoria:
                    puntos_item = categoria.puntos_fidelidad * item.cantidad
                    puntos_calculados_manual += puntos_item
                
                print(f"     - {producto.nombre} x{item.cantidad} = ${item.precio_unitario_venta * item.cantidad}")
                print(f"       SKU: {producto.sku}")
                print(f"       Categoría: {categoria.nombre if categoria else 'Sin categoría'}")
                print(f"       Puntos por categoría: {categoria.puntos_fidelidad if categoria else 0}")
                print(f"       Puntos de este item: {puntos_item}")
            
            print(f"\n   🧮 Verificación:")
            print(f"     Puntos calculados manualmente: {puntos_calculados_manual}")
            print(f"     Puntos registrados en pedido: {pedido.puntos_ganados}")
            
            if puntos_calculados_manual != pedido.puntos_ganados:
                print(f"     ❌ DISCREPANCIA DETECTADA")
                
                # Recalcular usando el servicio
                puntos_servicio = PuntosService.calcular_puntos_por_pedido(db, pedido.id)
                print(f"     Recálculo con PuntosService: {puntos_servicio}")
            else:
                print(f"     ✅ Cálculo consistente")
        
        print(f"\n✅ Búsqueda completada")
        
    except Exception as e:
        print(f"❌ Error durante búsqueda: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    buscar_pedido_60_puntos()