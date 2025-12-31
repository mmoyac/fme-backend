#!/usr/bin/env python3
"""
Script para verificar el cálculo histórico de puntos en ambos pedidos
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import MovimientoPuntos, Pedido
from datetime import datetime

def verificar_calculo_historico():
    db = SessionLocal()
    
    try:
        print("🔍 VERIFICANDO CÁLCULO HISTÓRICO DE PUNTOS")
        print("=" * 55)
        
        # Obtener los pedidos
        ped_26 = db.query(Pedido).filter(Pedido.id == 26).first()
        ped_27 = db.query(Pedido).filter(Pedido.id == 27).first()
        
        cliente_id = 1  # Marcelo
        
        print(f"\n📅 CRONOLOGÍA DE PEDIDOS:")
        print(f"   PED-00026: {ped_26.fecha_pedido}")
        print(f"   PED-00027: {ped_27.fecha_pedido}")
        
        # Simular cálculo para PED-00026
        print(f"\n🧮 CÁLCULO PARA PED-00026 (al momento de ese pedido):")
        movimientos_hasta_26 = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.cliente_id == cliente_id,
            MovimientoPuntos.fecha_movimiento <= ped_26.fecha_pedido
        ).order_by(MovimientoPuntos.fecha_movimiento.asc()).all()
        
        puntos_26 = 0
        print(f"   Movimientos hasta PED-00026:")
        for mov in movimientos_hasta_26:
            if mov.tipo_movimiento.value == 'GANADOS':
                puntos_26 += mov.puntos
                print(f"     + {mov.puntos} pts (GANADOS) = {puntos_26} pts")
            elif mov.tipo_movimiento.value == 'USADOS':
                puntos_26 -= mov.puntos
                print(f"     - {mov.puntos} pts (USADOS) = {puntos_26} pts")
        
        # Agregar puntos de este pedido si está confirmado
        if ped_26.estado in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
            if ped_26.puntos_ganados:
                puntos_26 += ped_26.puntos_ganados
                print(f"     + {ped_26.puntos_ganados} pts (ganados en PED-00026) = {puntos_26} pts")
        
        print(f"   ✅ Resultado PED-00026: {puntos_26} puntos disponibles")
        
        # Simular cálculo para PED-00027
        print(f"\n🧮 CÁLCULO PARA PED-00027 (al momento de ese pedido):")
        movimientos_hasta_27 = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.cliente_id == cliente_id,
            MovimientoPuntos.fecha_movimiento <= ped_27.fecha_pedido
        ).order_by(MovimientoPuntos.fecha_movimiento.asc()).all()
        
        puntos_27 = 0
        print(f"   Movimientos hasta PED-00027:")
        for mov in movimientos_hasta_27:
            if mov.tipo_movimiento.value == 'GANADOS':
                puntos_27 += mov.puntos
                print(f"     + {mov.puntos} pts (GANADOS) = {puntos_27} pts")
            elif mov.tipo_movimiento.value == 'USADOS':
                puntos_27 -= mov.puntos
                print(f"     - {mov.puntos} pts (USADOS) = {puntos_27} pts")
            elif mov.tipo_movimiento.value == 'AJUSTE':
                puntos_27 += mov.puntos
                print(f"     {'+' if mov.puntos > 0 else ''}{mov.puntos} pts (AJUSTE) = {puntos_27} pts")
        
        # Agregar puntos de este pedido si está confirmado
        if ped_27.estado in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
            if ped_27.puntos_ganados:
                puntos_27 += ped_27.puntos_ganados
                print(f"     + {ped_27.puntos_ganados} pts (ganados en PED-00027) = {puntos_27} pts")
            if ped_27.puntos_usados:
                puntos_27 -= ped_27.puntos_usados
                print(f"     - {ped_27.puntos_usados} pts (usados en PED-00027) = {puntos_27} pts")
        
        print(f"   ✅ Resultado PED-00027: {puntos_27} puntos disponibles")
        
        print(f"\n📋 RESUMEN FINAL:")
        print(f"   📄 Boleta PED-00026 mostrará: {puntos_26} puntos disponibles")
        print(f"   📄 Boleta PED-00027 mostrará: {puntos_27} puntos disponibles")
        print(f"   ✅ Cada boleta refleja el estado de puntos DESPUÉS de ese pedido")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_calculo_historico()