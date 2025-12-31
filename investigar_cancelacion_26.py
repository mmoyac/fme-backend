#!/usr/bin/env python3
"""
Script para investigar qué pasó con el pedido PED-00026 al cancelarlo.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido, MovimientoPuntos, PuntosCliente, TipoMovimientoPuntos
from services.puntos_service import PuntosService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def investigar_cancelacion_pedido_26():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔍 INVESTIGACIÓN: Cancelación del Pedido PED-00026 ===")
        
        # 1. Buscar pedido 26
        pedido = db.query(Pedido).filter(Pedido.id == 26).first()
        if not pedido:
            print("❌ No se encontró pedido con ID 26")
            return
        
        cliente = pedido.cliente
        
        print(f"📋 Estado actual del pedido:")
        print(f"   ID: {pedido.id}")
        print(f"   Estado: {pedido.estado}")
        print(f"   Cliente: {cliente.nombre} - {cliente.email}")
        print(f"   Puntos ganados registrados: {pedido.puntos_ganados}")
        print(f"   Inventario descontado: {pedido.inventario_descontado}")
        
        # 2. Ver estado de puntos del cliente
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        print(f"\n💰 Estado de puntos del cliente:")
        print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
        print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
        print(f"   Puntos totales usados: {puntos_cliente.puntos_totales_usados}")
        
        # 3. Ver todos los movimientos de puntos de este pedido
        movimientos = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id == pedido.id
        ).order_by(MovimientoPuntos.fecha_movimiento).all()
        
        print(f"\n📊 Movimientos de puntos para este pedido ({len(movimientos)}):")
        for mov in movimientos:
            print(f"   - {mov.tipo_movimiento.value}: {mov.puntos} puntos")
            print(f"     Fecha: {mov.fecha_movimiento}")
            print(f"     Descripción: {mov.descripcion}")
        
        # 4. Diagnóstico específico para cancelación
        print(f"\n🔬 DIAGNÓSTICO DE CANCELACIÓN:")
        
        if pedido.estado == 'CANCELADO':
            print(f"   ✅ El pedido está CANCELADO")
            
            # Buscar si hay un movimiento de ajuste (devolución)
            movimientos_ajuste = [m for m in movimientos if m.tipo_movimiento == TipoMovimientoPuntos.AJUSTE]
            movimientos_ganados = [m for m in movimientos if m.tipo_movimiento == TipoMovimientoPuntos.GANADOS]
            
            if movimientos_ganados:
                print(f"   ✅ Se encontraron {len(movimientos_ganados)} movimientos de puntos GANADOS")
                
                if movimientos_ajuste:
                    print(f"   ✅ Se encontraron {len(movimientos_ajuste)} movimientos de AJUSTE (devolución)")
                    
                    # Verificar si se devolvieron los puntos correctamente
                    puntos_ganados_total = sum(m.puntos for m in movimientos_ganados)
                    puntos_devueltos_total = sum(m.puntos for m in movimientos_ajuste)
                    
                    print(f"   📊 Puntos ganados: +{puntos_ganados_total}")
                    print(f"   📊 Puntos devueltos: {puntos_devueltos_total}")
                    
                    if abs(puntos_ganados_total + puntos_devueltos_total) < 0.01:  # Los ajustes son negativos
                        print(f"   ✅ Los puntos se devolvieron correctamente")
                    else:
                        print(f"   ❌ ERROR: No se devolvieron todos los puntos")
                        print(f"       Diferencia: {puntos_ganados_total + puntos_devueltos_total}")
                else:
                    print(f"   ❌ ERROR: NO se encontraron movimientos de AJUSTE")
                    print(f"       Los puntos NO se devolvieron al cancelar el pedido")
                    print(f"       Se esperaba un movimiento de -{sum(m.puntos for m in movimientos_ganados)} puntos")
            else:
                print(f"   ⚠️  No se encontraron movimientos de puntos GANADOS")
        else:
            print(f"   ❌ El pedido NO está cancelado, estado: {pedido.estado}")
        
        # 5. Verificar si necesita corrección
        if pedido.estado == 'CANCELADO' and movimientos_ganados and not movimientos_ajuste:
            print(f"\n🔧 RECOMENDACIÓN:")
            print(f"   Es necesario corregir este pedido devolviendo los puntos otorgados")
            puntos_a_devolver = sum(m.puntos for m in movimientos_ganados)
            print(f"   Puntos a devolver: {puntos_a_devolver}")
        
        print(f"\n✅ Investigación completada")
        
    except Exception as e:
        print(f"❌ Error durante investigación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    investigar_cancelacion_pedido_26()