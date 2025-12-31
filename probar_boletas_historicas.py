#!/usr/bin/env python3
"""
Script para probar que las boletas muestren los puntos correctos al momento de cada pedido
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido
from services.boleta_service import GeneradorBoleta

def probar_boletas_historicas():
    db = SessionLocal()
    try:
        print("🧪 PROBANDO BOLETAS CON PUNTOS HISTÓRICOS CORRECTOS")
        print("=" * 60)
        
        # Probar PED-00026
        print(f"\n📦 PROBANDO PED-00026:")
        ped_26 = db.query(Pedido).filter(Pedido.id == 26).first()
        if ped_26:
            print(f"   Estado: {ped_26.estado}")
            print(f"   Fecha: {ped_26.fecha_pedido}")
            print(f"   Puntos ganados: {ped_26.puntos_ganados}")
            print(f"   Puntos usados: {ped_26.puntos_usados}")
            
            print(f"   💡 Cálculo esperado:")
            print(f"      Antes del pedido: 0 puntos")
            print(f"      + Ganó en este pedido: {ped_26.puntos_ganados} puntos")
            print(f"      = Después del pedido: {ped_26.puntos_ganados} puntos")
            print(f"      ✅ Debería mostrar: {ped_26.puntos_ganados} puntos disponibles")
            
            # Generar boleta
            generador = GeneradorBoleta()
            buffer_pdf = generador.generar_boleta(ped_26)
            
            # Guardar
            import os
            filename = "static/boletas/PED-00026-historico.pdf"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(buffer_pdf.getvalue())
            print(f"   ✅ Boleta generada: {filename}")
        
        # Probar PED-00027
        print(f"\n📦 PROBANDO PED-00027:")
        ped_27 = db.query(Pedido).filter(Pedido.id == 27).first()
        if ped_27:
            print(f"   Estado: {ped_27.estado}")
            print(f"   Fecha: {ped_27.fecha_pedido}")
            print(f"   Puntos ganados: {ped_27.puntos_ganados}")
            print(f"   Puntos usados: {ped_27.puntos_usados}")
            
            print(f"   💡 Cálculo esperado:")
            print(f"      Antes del pedido: 8 puntos (del PED-00026)")
            print(f"      - Usó en este pedido: {ped_27.puntos_usados} puntos")
            print(f"      + Ganó en este pedido: {ped_27.puntos_ganados} puntos")
            print(f"      = Después del pedido: 8 - {ped_27.puntos_usados} + {ped_27.puntos_ganados} = 11 puntos")
            print(f"      ✅ Debería mostrar: 11 puntos disponibles")
            
            # Generar boleta
            generador = GeneradorBoleta()
            buffer_pdf = generador.generar_boleta(ped_27)
            
            # Guardar
            import os
            filename = "static/boletas/PED-00027-historico.pdf"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(buffer_pdf.getvalue())
            print(f"   ✅ Boleta generada: {filename}")
        
        print(f"\n📋 RESUMEN:")
        print(f"   ✅ PED-00026: Debe mostrar 8 puntos disponibles")
        print(f"   ✅ PED-00027: Debe mostrar 11 puntos disponibles")
        print(f"   💡 Cada boleta muestra los puntos DESPUÉS de procesar ese pedido")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    probar_boletas_historicas()