#!/usr/bin/env python3
"""
Script para corregir completamente el PED-00027 - limpiar puntos usados
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido

def corregir_ped_27_puntos_usados():
    db = SessionLocal()
    
    try:
        print("🔧 CORRIGIENDO PED-00027 - LIMPIANDO PUNTOS USADOS")
        print("=" * 60)
        
        # Obtener PED-00027
        ped_27 = db.query(Pedido).filter(Pedido.id == 27).first()
        if not ped_27:
            print("❌ No se encontró PED-00027")
            return
        
        print(f"📦 PED-00027 ANTES:")
        print(f"   Estado: {ped_27.estado}")
        print(f"   Puntos ganados: {ped_27.puntos_ganados}")
        print(f"   Puntos usados: {ped_27.puntos_usados}")
        print(f"   Descuento por puntos: ${ped_27.descuento_puntos}")
        
        # Como está PENDIENTE, no debería tener puntos usados ni descuento
        if ped_27.estado == 'PENDIENTE':
            ped_27.puntos_usados = 0
            ped_27.descuento_puntos = 0.00
            
            # Recalcular el monto total (agregar el descuento de vuelta)
            ped_27.monto_total = 6000.00  # Precio original del queso
        
        db.commit()
        
        print(f"\n📦 PED-00027 DESPUÉS:")
        print(f"   Estado: {ped_27.estado}")
        print(f"   Puntos ganados: {ped_27.puntos_ganados}")
        print(f"   Puntos usados: {ped_27.puntos_usados}")
        print(f"   Descuento por puntos: ${ped_27.descuento_puntos}")
        print(f"   Monto total: ${ped_27.monto_total}")
        
        print(f"\n✅ CORRECCIÓN COMPLETADA")
        print(f"Ahora cuando se confirme el PED-00027:")
        print(f"   - Otorgará: 8 puntos (por el queso)")
        print(f"   - Descontará: 0 puntos (no usa puntos)")
        print(f"   - Saldo final esperado: 8 + 8 = 16 puntos")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_ped_27_puntos_usados()