#!/usr/bin/env python3
"""
Script para simular exactamente el cálculo de puntos cuando se crea un pedido con queso.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Producto, CategoriaProducto, ItemPedido, Pedido, Local, Cliente
from services.puntos_service import PuntosService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_calculo_queso():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔍 DEBUG: Cálculo de puntos para queso ===")
        
        # 1. Buscar producto queso
        queso = db.query(Producto).filter(Producto.nombre.ilike('%queso%')).first()
        if not queso:
            print("❌ No se encontró producto con 'queso' en el nombre")
            return
        
        print(f"✅ Producto encontrado: {queso.nombre} (ID: {queso.id}, SKU: {queso.sku})")
        print(f"   Categoría ID: {queso.categoria_id}")
        
        # 2. Ver información de la categoría
        categoria = queso.categoria
        if not categoria:
            print("❌ El producto no tiene categoría asignada")
            return
        
        print(f"✅ Categoría: {categoria.nombre} (ID: {categoria.id})")
        print(f"   Puntos fidelidad: {categoria.puntos_fidelidad}")
        
        # 3. Crear un pedido simulado para probar el cálculo
        print(f"\n--- Simulando cálculo de puntos ---")
        
        # Buscar cliente y local existente
        cliente = db.query(Cliente).first()
        local = db.query(Local).first()
        
        if not cliente or not local:
            print("❌ No hay cliente o local en la base de datos")
            return
        
        # Crear pedido temporal (sin commit)
        pedido = Pedido(
            cliente_id=cliente.id,
            local_id=local.id,
            monto_total=6000,
            estado="PENDIENTE"
        )
        db.add(pedido)
        db.flush()  # Para obtener ID sin hacer commit
        
        # Crear item temporal con 1 queso
        item = ItemPedido(
            pedido_id=pedido.id,
            producto_id=queso.id,
            cantidad=1,
            precio_unitario_venta=6000
        )
        db.add(item)
        db.flush()
        
        # 4. Calcular puntos usando el servicio
        puntos_calculados = PuntosService.calcular_puntos_por_pedido(db, pedido.id)
        
        print(f"🧮 Cálculo manual:")
        print(f"   Categoría '{categoria.nombre}' tiene {categoria.puntos_fidelidad} puntos")
        print(f"   Cantidad de queso: 1")
        print(f"   Puntos esperados: {categoria.puntos_fidelidad} × 1 = {categoria.puntos_fidelidad}")
        
        print(f"\n🎯 Resultado del PuntosService:")
        print(f"   Puntos calculados: {puntos_calculados}")
        
        if puntos_calculados == categoria.puntos_fidelidad:
            print("✅ El cálculo es CORRECTO")
        else:
            print(f"❌ ERROR: Se esperaba {categoria.puntos_fidelidad} pero se calculó {puntos_calculados}")
        
        # 5. Verificar si hay algo raro en el item
        items_query = (
            db.query(ItemPedido)
            .join(Producto, ItemPedido.producto_id == Producto.id)
            .filter(ItemPedido.pedido_id == pedido.id)
            .all()
        )
        
        print(f"\n📋 Items en el pedido:")
        for item in items_query:
            cat = item.producto.categoria
            puntos_item = cat.puntos_fidelidad * item.cantidad if cat else 0
            print(f"   - {item.producto.nombre}: cantidad={item.cantidad}, precio=${item.precio_unitario_venta}")
            print(f"     Categoría: {cat.nombre if cat else 'Sin categoría'}")
            print(f"     Puntos categoría: {cat.puntos_fidelidad if cat else 0}")
            print(f"     Puntos item: {puntos_item}")
        
        # 6. Rollback para no guardar el pedido temporal
        db.rollback()
        
        print(f"\n--- Verificando otros productos de Lácteos ---")
        productos_lacteos = db.query(Producto).filter(Producto.categoria_id == categoria.id).all()
        print(f"Productos en categoría '{categoria.nombre}':")
        for prod in productos_lacteos:
            print(f"   - {prod.nombre} (SKU: {prod.sku})")
        
        print(f"\n✅ Debug completado")
        
    except Exception as e:
        print(f"❌ Error durante debug: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_calculo_queso()