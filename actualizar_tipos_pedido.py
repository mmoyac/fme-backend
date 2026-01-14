#!/usr/bin/env python3
"""
Script para actualizar tipos de pedido en la base de datos.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def actualizar_tipos_pedido():
    """Actualiza los tipos de pedido según los requisitos."""
    db: Session = SessionLocal()
    
    try:
        print("🔄 Actualizando tipos de pedido...")
        
        # 1. Marcar pedido PED-00042 (id=42) como tipo CAJAS_VARIABLES (2)
        pedido_42 = db.query(Pedido).filter(Pedido.id == 42).first()
        if pedido_42:
            pedido_42.tipo_pedido_id = 2
            print(f"✅ Pedido PED-00042 marcado como tipo CAJAS_VARIABLES (2)")
        else:
            print(f"⚠️ Pedido PED-00042 no encontrado")
        
        # 2. Marcar todos los demás pedidos como tipo PRODUCTOS (1)
        pedidos_actualizados = db.query(Pedido).filter(Pedido.id != 42).update(
            {Pedido.tipo_pedido_id: 1}
        )
        print(f"✅ {pedidos_actualizados} pedidos marcados como tipo PRODUCTOS (1)")
        
        # 3. Confirmar cambios
        db.commit()
        print(f"✅ Cambios guardados exitosamente")
        
        # 4. Verificar resultados
        print(f"\n📊 Resumen de tipos de pedido:")
        pedidos_tipo_1 = db.query(Pedido).filter(Pedido.tipo_pedido_id == 1).count()
        pedidos_tipo_2 = db.query(Pedido).filter(Pedido.tipo_pedido_id == 2).count()
        print(f"   Tipo PRODUCTOS (1): {pedidos_tipo_1} pedidos")
        print(f"   Tipo CAJAS_VARIABLES (2): {pedidos_tipo_2} pedidos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_tipos_pedido()