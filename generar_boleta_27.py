#!/usr/bin/env python3
"""
Script para generar boleta del PED-00027 y verificar puntos
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Pedido
from services.boleta_service import GeneradorBoleta
import os

def generar_boleta_ped_27():
    db = SessionLocal()
    try:
        print("📄 GENERANDO BOLETA PED-00027")
        print("=" * 40)
        
        # Obtener el pedido
        pedido = db.query(Pedido).filter(Pedido.id == 27).first()
        if not pedido:
            print("❌ Pedido no encontrado")
            return
        
        # Generar boleta
        generador_boleta = GeneradorBoleta()
        archivo_pdf = generador_boleta.generar_boleta(pedido)
        
        print(f"✅ Boleta generada: {archivo_pdf}")
        
        # Verificar si el archivo existe
        if os.path.exists(archivo_pdf):
            size = os.path.getsize(archivo_pdf)
            print(f"📄 Tamaño del archivo: {size} bytes")
        else:
            print("❌ Archivo no encontrado")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generar_boleta_ped_27()