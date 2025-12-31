#!/usr/bin/env python3
"""
Script para simular confirmar el PED-00027 con uso de puntos y verificar el resultado
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido, Cliente, PuntosCliente

def simular_confirmar_ped_27():
    db = SessionLocal()
    
    try:
        print("🧪 SIMULANDO CONFIRMACIÓN DEL PED-00027")
        print("=" * 60)
        
        # Obtener estado antes
        marcelo = db.query(Cliente).filter(Cliente.nombre.ilike('%marcelo%')).first()
        puntos_cliente_antes = db.query(PuntosCliente).filter(PuntosCliente.cliente_id == marcelo.id).first()
        
        print(f"📊 ESTADO ANTES DE CONFIRMAR:")
        print(f"   Marcelo - Puntos disponibles: {puntos_cliente_antes.puntos_disponibles}")
        
        ped_27_antes = db.query(Pedido).filter(Pedido.id == 27).first()
        print(f"   PED-00027 - Estado: {ped_27_antes.estado}")
        print(f"   PED-00027 - Puntos ganados: {ped_27_antes.puntos_ganados}")
        print(f"   PED-00027 - Puntos usados: {ped_27_antes.puntos_usados}")
        
        # Configurar el pedido para usar 5 puntos
        print(f"\n🔧 CONFIGURANDO PED-00027 PARA USAR 5 PUNTOS:")
        ped_27_antes.puntos_usados = 5
        ped_27_antes.descuento_puntos = 5.00
        ped_27_antes.monto_total = 5995.00  # 6000 - 5
        db.commit()
        
        print(f"   ✅ Puntos usados configurados: 5")
        print(f"   ✅ Descuento configurado: $5")
        print(f"   ✅ Total ajustado: ${ped_27_antes.monto_total}")
        
        # Simular confirmación usando el servicio de puntos
        from services.puntos_service import PuntosService
        
        print(f"\n🚀 SIMULANDO CONFIRMACIÓN (manual)...")
        
        # 1. Usar los 5 puntos
        if ped_27_antes.puntos_usados > 0:
            from decimal import Decimal
            exito, mensaje, movimiento = PuntosService.usar_puntos_en_pedido(
                db,
                marcelo.id,
                27,
                5,
                Decimal("5.00")
            )
            
            if exito:
                print(f"   ✅ Puntos usados exitosamente: {mensaje}")
            else:
                print(f"   ❌ Error usando puntos: {mensaje}")
                return
        
        # 2. Otorgar los 8 puntos ganados
        if ped_27_antes.puntos_ganados > 0:
            PuntosService.otorgar_puntos_por_pedido(
                db,
                marcelo.id,
                27,
                8,
                f"Puntos ganados por confirmación de pedido #27"
            )
            print(f"   ✅ Puntos otorgados: 8")
        
        # 3. Cambiar estado a CONFIRMADO
        ped_27_antes.estado = "CONFIRMADO"
        
        db.commit()
        
        # Obtener estado después
        db.refresh(puntos_cliente_antes)
        
        print(f"\n📊 ESTADO DESPUÉS DE CONFIRMAR:")
        print(f"   Marcelo - Puntos disponibles: {puntos_cliente_antes.puntos_disponibles}")
        print(f"   PED-00027 - Estado: {ped_27_antes.estado}")
        
        print(f"\n🧮 CÁLCULO ESPERADO:")
        print(f"   Puntos iniciales: 8")
        print(f"   - Puntos usados: -5")
        print(f"   + Puntos ganados: +8")
        print(f"   = Total esperado: 11 puntos")
        
        print(f"\n📋 RESUMEN:")
        if puntos_cliente_antes.puntos_disponibles == 11:
            print(f"   ✅ ¡PERFECTO! Marcelo tiene {puntos_cliente_antes.puntos_disponibles} puntos")
            print(f"   ✅ PED-00026: 8 puntos ganados")
            print(f"   ✅ PED-00027: 8 puntos ganados - 5 puntos usados = +3 netos")
            print(f"   ✅ Total: 8 + 3 = 11 puntos ✅")
        else:
            print(f"   ❌ Error: Marcelo debería tener 11 puntos, pero tiene {puntos_cliente_antes.puntos_disponibles}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    simular_confirmar_ped_27()