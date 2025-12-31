#!/usr/bin/env python3
"""
Script para generar y guardar la boleta del PED-00027 como archivo PDF
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido
from services.boleta_service import GeneradorBoleta

def guardar_boleta_ped_27():
    db = SessionLocal()
    try:
        print("📄 GENERANDO Y GUARDANDO BOLETA PED-00027")
        print("=" * 50)
        
        # Obtener el pedido
        pedido = db.query(Pedido).filter(Pedido.id == 27).first()
        if not pedido:
            print("❌ Pedido no encontrado")
            return
        
        print(f"📦 Pedido encontrado:")
        print(f"   ID: {pedido.id}")
        print(f"   Cliente ID: {pedido.cliente_id}")
        print(f"   Estado: {pedido.estado}")
        print(f"   Total: ${pedido.monto_total:,.0f}")
        print(f"   Puntos ganados: {pedido.puntos_ganados}")
        print(f"   Puntos usados: {pedido.puntos_usados}")
        print(f"   Descuento: ${pedido.descuento_puntos}")
        
        # Verificar puntos disponibles del cliente
        from services.puntos_service import PuntosService
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, pedido.cliente_id)
        print(f"   Puntos disponibles del cliente: {puntos_cliente.puntos_disponibles}")
        
        # Generar boleta en memoria
        generador_boleta = GeneradorBoleta()
        buffer_pdf = generador_boleta.generar_boleta(pedido)
        
        # Guardar en archivo
        filename = f"static/boletas/PED-00027-test.pdf"
        
        # Crear directorio si no existe
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(buffer_pdf.getvalue())
        
        print(f"\n✅ Boleta guardada en: {filename}")
        
        # Verificar tamaño del archivo
        import os
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"📄 Tamaño del archivo: {size} bytes")
            
            print(f"\n📋 CONTENIDO ESPERADO EN LA BOLETA:")
            print(f"   • Subtotal: $6,000")
            print(f"   • Descuento puntos (5 pts): -$5")
            print(f"   • TOTAL: $5,995")
            print(f"   • Puntos ganados ✓: +8 pts")
            print(f"   • Puntos disponibles: {puntos_cliente.puntos_disponibles} pts")
            
        else:
            print("❌ Error: No se pudo guardar el archivo")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    guardar_boleta_ped_27()