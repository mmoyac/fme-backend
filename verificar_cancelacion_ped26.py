#!/usr/bin/env python3
"""
Script para verificar el estado del PED-00026 después de cancelación
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido, Cliente, PuntosCliente, MovimientoPuntos

def verificar_cancelacion_ped_26():
    db = SessionLocal()
    
    try:
        print("🔍 VERIFICANDO CANCELACIÓN DEL PED-00026")
        print("=" * 50)
        
        # Obtener el pedido 26
        ped_26 = db.query(Pedido).filter(Pedido.id == 26).first()
        if not ped_26:
            print("❌ Pedido 26 no encontrado")
            return
        
        print(f"📦 PED-00026:")
        print(f"   Estado: {ped_26.estado}")
        print(f"   Puntos ganados: {ped_26.puntos_ganados}")
        print(f"   Puntos usados: {ped_26.puntos_usados}")
        
        # Verificar estado de Marcelo
        marcelo = db.query(Cliente).filter(Cliente.nombre.ilike('%marcelo%')).first()
        puntos_cliente = db.query(PuntosCliente).filter(PuntosCliente.cliente_id == marcelo.id).first()
        
        print(f"\n👤 MARCELO:")
        print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
        print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
        
        # Revisar movimientos recientes
        print(f"\n📝 MOVIMIENTOS RECIENTES (últimos 5):")
        movimientos_recientes = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.cliente_id == marcelo.id
        ).order_by(MovimientoPuntos.fecha_movimiento.desc()).limit(5).all()
        
        for mov in movimientos_recientes:
            print(f"   {mov.fecha_movimiento.strftime('%H:%M:%S')} - {mov.tipo_movimiento.value}: {mov.puntos} pts - {mov.descripcion}")
        
        # Análisis
        if ped_26.estado == 'CANCELADO':
            print(f"\n🎯 ANÁLISIS:")
            print(f"   ✅ PED-00026 está CANCELADO")
            print(f"   💡 Si había otorgado puntos, deberían haberse devuelto")
            print(f"   📄 La boleta debería mostrar:")
            print(f"      - Estado: CANCELADO")
            print(f"      - Puntos que se habían ganado: {ped_26.puntos_ganados} (pero devueltos)")
            print(f"      - Información de devolución")
        else:
            print(f"\n⚠️  PED-00026 NO está cancelado (Estado: {ped_26.estado})")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_cancelacion_ped_26()