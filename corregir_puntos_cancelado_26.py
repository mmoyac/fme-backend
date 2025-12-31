#!/usr/bin/env python3
"""
Script para corregir manualmente el pedido PED-00026 devolviendo los puntos duplicados.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido, MovimientoPuntos, TipoMovimientoPuntos
from services.puntos_service import PuntosService
from datetime import datetime

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def corregir_puntos_pedido_26():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔧 CORRECCIÓN: Devolver puntos del pedido PED-00026 ===")
        
        # 1. Buscar pedido 26
        pedido = db.query(Pedido).filter(Pedido.id == 26).first()
        if not pedido:
            print("❌ No se encontró pedido con ID 26")
            return
        
        cliente = pedido.cliente
        
        print(f"📋 Estado actual:")
        print(f"   Pedido: {pedido.id} - Estado: {pedido.estado}")
        print(f"   Cliente: {cliente.nombre}")
        print(f"   Puntos ganados registrados en pedido: {pedido.puntos_ganados}")
        
        # 2. Ver estado actual de puntos del cliente
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        print(f"   Puntos disponibles del cliente: {puntos_cliente.puntos_disponibles}")
        print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
        
        # 3. Ver movimientos actuales de este pedido
        movimientos = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id == pedido.id
        ).all()
        
        print(f"\n📊 Movimientos actuales ({len(movimientos)}):")
        total_ganados = 0
        for mov in movimientos:
            print(f"   - {mov.tipo_movimiento.value}: {mov.puntos} puntos")
            if mov.tipo_movimiento == TipoMovimientoPuntos.GANADOS:
                total_ganados += mov.puntos
        
        print(f"\n🧮 Total puntos ganados por este pedido: {total_ganados}")
        
        # 4. Como el pedido está CANCELADO, devolver TODOS los puntos ganados
        if pedido.estado == "CANCELADO" and total_ganados > 0:
            print(f"\n🎯 Devolviendo {total_ganados} puntos...")
            
            # Crear movimiento de devolución
            movimiento_devolucion = MovimientoPuntos(
                cliente_id=pedido.cliente_id,
                pedido_id=pedido.id,
                tipo_movimiento=TipoMovimientoPuntos.AJUSTE,
                puntos=-total_ganados,  # Negativo para devolver
                descripcion=f"Corrección: Devolución por cancelación de pedido #{pedido.id}",
                fecha_movimiento=datetime.now()
            )
            db.add(movimiento_devolucion)
            
            # Actualizar puntos del cliente
            puntos_cliente.puntos_disponibles -= total_ganados
            puntos_cliente.puntos_totales_ganados -= total_ganados
            
            # Asegurar que no quede negativo
            if puntos_cliente.puntos_disponibles < 0:
                puntos_cliente.puntos_disponibles = 0
            if puntos_cliente.puntos_totales_ganados < 0:
                puntos_cliente.puntos_totales_ganados = 0
            
            # Guardar cambios
            db.commit()
            print(f"   ✅ Puntos devueltos exitosamente")
            
            # 5. Verificar estado final
            db.refresh(puntos_cliente)
            print(f"\n📊 Estado final:")
            print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
            print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
            
            # Ver todos los movimientos después de la corrección
            movimientos_final = db.query(MovimientoPuntos).filter(
                MovimientoPuntos.pedido_id == pedido.id
            ).order_by(MovimientoPuntos.fecha_movimiento).all()
            
            print(f"\n📊 Movimientos finales ({len(movimientos_final)}):")
            for mov in movimientos_final:
                print(f"   - {mov.tipo_movimiento.value}: {mov.puntos} puntos")
                print(f"     {mov.descripcion}")
                
        else:
            print(f"\n⚠️  No se requiere corrección:")
            print(f"   Estado del pedido: {pedido.estado}")
            print(f"   Puntos ganados: {total_ganados}")
        
        print(f"\n✅ Corrección completada")
        
    except Exception as e:
        print(f"❌ Error durante corrección: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_puntos_pedido_26()