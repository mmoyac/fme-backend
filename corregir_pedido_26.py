#!/usr/bin/env python3
"""
Script para corregir el pedido PED-00026 y otorgar los puntos correspondientes.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido
from services.puntos_service import PuntosService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def corregir_pedido_26():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔧 CORRECCIÓN: Pedido PED-00026 ===")
        
        # 1. Buscar pedido 26
        pedido = db.query(Pedido).filter(Pedido.id == 26).first()
        if not pedido:
            print("❌ No se encontró pedido con ID 26")
            return
        
        print(f"📋 Pedido encontrado:")
        print(f"   Cliente: {pedido.cliente.nombre}")
        print(f"   Estado: {pedido.estado}")
        print(f"   Puntos ganados actuales: {pedido.puntos_ganados}")
        
        # 2. Calcular puntos correctos
        puntos_correctos = PuntosService.calcular_puntos_por_pedido(db, pedido.id)
        print(f"   Puntos que debería tener: {puntos_correctos}")
        
        if puntos_correctos > 0:
            # 3. Actualizar el campo puntos_ganados en el pedido
            pedido.puntos_ganados = puntos_correctos
            print(f"   ✅ Actualizando puntos_ganados a {puntos_correctos}")
            
            # 4. Si el pedido está confirmado, otorgar los puntos al cliente
            if pedido.estado == 'CONFIRMADO':
                print(f"   🎯 Otorgando {puntos_correctos} puntos al cliente...")
                
                movimiento = PuntosService.otorgar_puntos_por_pedido(
                    db,
                    pedido.cliente_id,
                    pedido.id,
                    puntos_correctos,
                    f"Corrección: Puntos ganados por pedido #{pedido.id}"
                )
                
                if movimiento:
                    print(f"   ✅ Puntos otorgados exitosamente")
                    print(f"   📊 Movimiento ID: {movimiento.id}")
                else:
                    print(f"   ❌ Error al otorgar puntos")
            else:
                print(f"   ⏳ Pedido no confirmado, puntos quedan pendientes")
            
            # 5. Guardar cambios
            db.commit()
            print(f"\n✅ Corrección completada")
            
            # 6. Verificar estado final
            db.refresh(pedido)
            puntos_cliente = PuntosService.obtener_puntos_cliente(db, pedido.cliente_id)
            
            print(f"\n📊 Estado final:")
            print(f"   Puntos ganados en pedido: {pedido.puntos_ganados}")
            print(f"   Puntos disponibles del cliente: {puntos_cliente.puntos_disponibles}")
            print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
            
        else:
            print(f"   ❌ El pedido no genera puntos")
        
    except Exception as e:
        print(f"❌ Error durante corrección: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_pedido_26()