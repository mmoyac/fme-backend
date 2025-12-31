#!/usr/bin/env python3
"""
Script para generar y verificar la boleta del PED-00026 cancelado
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido
from services.boleta_service import GeneradorBoleta

def generar_boleta_cancelada():
    db = SessionLocal()
    try:
        print("📄 GENERANDO BOLETA DEL PED-00026 CANCELADO")
        print("=" * 55)
        
        # Obtener el pedido cancelado
        ped_26 = db.query(Pedido).filter(Pedido.id == 26).first()
        if not ped_26:
            print("❌ Pedido no encontrado")
            return
        
        print(f"📦 PED-00026:")
        print(f"   Estado: {ped_26.estado}")
        print(f"   Total: ${ped_26.monto_total:,.0f}")
        print(f"   Puntos ganados: {ped_26.puntos_ganados}")
        print(f"   Puntos usados: {ped_26.puntos_usados}")
        
        # Verificar puntos actuales del cliente
        from services.puntos_service import PuntosService
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, ped_26.cliente_id)
        print(f"   Puntos actuales del cliente: {puntos_cliente.puntos_disponibles}")
        
        # Generar boleta
        generador = GeneradorBoleta()
        buffer_pdf = generador.generar_boleta(ped_26)
        
        # Guardar
        import os
        filename = "static/boletas/PED-00026-cancelado.pdf"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(buffer_pdf.getvalue())
        
        print(f"\n✅ Boleta generada: {filename}")
        print(f"📄 Tamaño: {len(buffer_pdf.getvalue())} bytes")
        
        print(f"\n📋 CONTENIDO ESPERADO EN LA BOLETA CANCELADA:")
        print(f"   • TOTAL: $6,000")
        print(f"   • Puntos devueltos: -8 pts")
        print(f"   • ⚠️ PEDIDO CANCELADO")
        print(f"   • Puntos actuales: {puntos_cliente.puntos_disponibles} pts")
        
        print(f"\n💡 EXPLICACIÓN:")
        print(f"   • El pedido había otorgado 8 puntos")
        print(f"   • Al cancelarse, se devolvieron esos 8 puntos")
        print(f"   • Marcelo ahora tiene {puntos_cliente.puntos_disponibles} puntos")
        print(f"   • La boleta refleja esta devolución")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generar_boleta_cancelada()