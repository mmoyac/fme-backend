#!/usr/bin/env python3
"""
Script para actualizar pedidos existentes con medio de pago por defecto.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importaciones
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy.orm import Session
from database.database import SessionLocal, engine
from database.models import Pedido, MedioPago


def actualizar_pedidos_sin_medio_pago():
    """Actualizar pedidos que no tienen medio de pago asignado."""
    db = SessionLocal()
    
    try:
        # Buscar medio de pago MercadoPago
        mp = db.query(MedioPago).filter(MedioPago.codigo == 'MERCADOPAGO').first()
        if not mp:
            print("❌ No se encontró el medio de pago MERCADOPAGO")
            return
        
        # Buscar pedidos sin medio de pago
        pedidos_sin_medio = db.query(Pedido).filter(Pedido.medio_pago_id.is_(None)).all()
        
        print(f"📊 Encontrados {len(pedidos_sin_medio)} pedidos sin medio de pago")
        
        # Actualizar cada pedido
        for pedido in pedidos_sin_medio:
            pedido.medio_pago_id = mp.id
            print(f"  ✅ Pedido {pedido.id} actualizado con MercadoPago")
        
        db.commit()
        print(f"\n✅ {len(pedidos_sin_medio)} pedidos actualizados exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        
    finally:
        db.close()


if __name__ == "__main__":
    actualizar_pedidos_sin_medio_pago()