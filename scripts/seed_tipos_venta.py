#!/usr/bin/env python3
"""
Script para cargar datos iniciales de TipoVenta.
"""
import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import TipoVenta

def seed_tipos_venta():
    """Insertar tipos de venta iniciales."""
    db = next(get_db())
    
    # Verificar si ya existen tipos de venta
    existing_count = db.query(TipoVenta).count()
    if existing_count > 0:
        print(f"✅ Ya existen {existing_count} tipos de venta. No se insertarán duplicados.")
        return
    
    tipos_venta = [
        {
            "codigo": "UNITARIO",
            "nombre": "Por Unidad",
            "descripcion": "Productos que se venden por cantidad de unidades (ej: pan, pasteles)",
            "activo": True
        },
        {
            "codigo": "PESO_SUELTO", 
            "nombre": "Por Peso Suelto",
            "descripcion": "Productos que se venden por peso en gramos/kilogramos (ej: quesos, fiambres)",
            "activo": True
        },
        {
            "codigo": "CAJA_VARIABLE",
            "nombre": "Caja Variable", 
            "descripcion": "Productos en cajas con peso variable que requieren trazabilidad (ej: carnes)",
            "activo": True
        }
    ]
    
    print("🔄 Insertando tipos de venta...")
    
    for tipo_data in tipos_venta:
        tipo = TipoVenta(**tipo_data)
        db.add(tipo)
        print(f"   ➕ {tipo_data['codigo']}: {tipo_data['nombre']}")
    
    try:
        db.commit()
        print("✅ Tipos de venta insertados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar tipos de venta: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_tipos_venta()