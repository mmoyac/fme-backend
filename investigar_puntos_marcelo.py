#!/usr/bin/env python3
"""
Script para investigar el problema de puntos de Marcelo
PED-00026: Ganó 8 puntos
PED-00027: Ganó 8 puntos, usó 5 puntos
Saldo esperado: 11 puntos, pero tiene solo 3
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Cliente, Pedido, MovimientoPuntos, PuntosCliente
from sqlalchemy.orm import joinedload

def investigar_puntos_marcelo():
    db = SessionLocal()
    
    try:
        print("🔍 INVESTIGANDO PROBLEMA DE PUNTOS DE MARCELO")
        print("=" * 60)
        
        # 1. Buscar cliente Marcelo
        print("\n1. INFORMACIÓN DEL CLIENTE:")
        marcelo = db.query(Cliente).filter(
            Cliente.nombre.ilike('%marcelo%')
        ).first()
        
        if not marcelo:
            print("❌ No se encontró cliente Marcelo")
            return
            
        print(f"Cliente: {marcelo.nombre} (ID: {marcelo.id})")
        print(f"Email: {marcelo.email}")
        
        # 2. Estado actual de puntos
        print("\n2. ESTADO ACTUAL DE PUNTOS:")
        puntos_cliente = db.query(PuntosCliente).filter(
            PuntosCliente.cliente_id == marcelo.id
        ).first()
        
        if puntos_cliente:
            print(f"Puntos disponibles: {puntos_cliente.puntos_disponibles}")
            print(f"Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
            print(f"Puntos totales usados: {puntos_cliente.puntos_totales_usados}")
        else:
            print("❌ No se encontró registro de puntos para este cliente")
        
        # 3. Pedidos de Marcelo (especialmente PED-00026 y PED-00027)
        print("\n3. PEDIDOS DE MARCELO:")
        pedidos = db.query(Pedido).filter(
            Pedido.cliente_id == marcelo.id
        ).order_by(Pedido.id.desc()).all()
        
        for pedido in pedidos:
            print(f"\n📦 Pedido PED-{pedido.id:05d}:")
            print(f"   Estado: {pedido.estado}")
            print(f"   Total: ${pedido.monto_total:,.0f}")
            print(f"   Puntos ganados: {pedido.puntos_ganados}")
            print(f"   Puntos usados: {pedido.puntos_usados}")
            print(f"   Fecha: {pedido.fecha_pedido}")
        
        # 4. Historial completo de movimientos de puntos
        print(f"\n4. HISTORIAL DE MOVIMIENTOS DE PUNTOS (Cliente ID: {marcelo.id}):")
        movimientos = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.cliente_id == marcelo.id
        ).order_by(MovimientoPuntos.fecha_movimiento.asc()).all()
        
        saldo_calculado = 0
        for i, mov in enumerate(movimientos):
            print(f"\n📝 Movimiento #{i+1}:")
            print(f"   Tipo: {mov.tipo_movimiento}")
            print(f"   Puntos: {mov.puntos}")
            print(f"   Pedido: {mov.pedido_id}")
            print(f"   Fecha: {mov.fecha_movimiento}")
            print(f"   Descripción: {mov.descripcion}")
            
            if mov.tipo_movimiento in ['GANADO', 'DEVOLUCION']:
                saldo_calculado += mov.puntos
                print(f"   ✅ Saldo después: +{saldo_calculado}")
            elif mov.tipo_movimiento == 'USADO':
                saldo_calculado -= mov.puntos
                print(f"   ➖ Saldo después: -{saldo_calculado}")
        
        print(f"\n📊 RESUMEN DEL CÁLCULO:")
        print(f"Saldo calculado manualmente: {saldo_calculado}")
        print(f"Saldo en base de datos: {puntos_cliente.puntos_disponibles if puntos_cliente else 'N/A'}")
        print(f"¿Coinciden? {'✅ SÍ' if puntos_cliente and saldo_calculado == puntos_cliente.puntos_disponibles else '❌ NO'}")
        
        # 5. Verificar pedidos específicos PED-00026 y PED-00027
        print(f"\n5. ANÁLISIS ESPECÍFICO DE PED-00026 Y PED-00027:")
        ped_26 = db.query(Pedido).filter(Pedido.id == 26).first()
        ped_27 = db.query(Pedido).filter(Pedido.id == 27).first()
        
        if ped_26:
            print(f"\n📦 PED-00026 (ID: {ped_26.id}):")
            print(f"   Cliente ID: {ped_26.cliente_id}")
            print(f"   Estado: {ped_26.estado}")
            print(f"   Puntos ganados: {ped_26.puntos_ganados}")
            print(f"   Puntos usados: {ped_26.puntos_usados}")
        
        if ped_27:
            print(f"\n📦 PED-00027 (ID: {ped_27.id}):")
            print(f"   Cliente ID: {ped_27.cliente_id}")
            print(f"   Estado: {ped_27.estado}")
            print(f"   Puntos ganados: {ped_27.puntos_ganados}")
            print(f"   Puntos usados: {ped_27.puntos_usados}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    investigar_puntos_marcelo()