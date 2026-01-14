#!/usr/bin/env python3
"""
Script para cargar datos iniciales de TipoProveedor.
"""
import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import TipoProveedor

def seed_tipos_proveedor():
    """Insertar tipos de proveedor iniciales."""
    db = next(get_db())
    
    # Verificar si ya existen tipos de proveedor
    existing_count = db.query(TipoProveedor).count()
    if existing_count > 0:
        print(f"✅ Ya existen {existing_count} tipos de proveedor. No se insertarán duplicados.")
        return
    
    tipos_proveedor = [
        {
            "codigo": "CARNES",
            "nombre": "Frigoríficos y Carnes",
            "descripcion": "Proveedores de productos cárnicos, frigoríficos, mataderos",
            "activo": True
        },
        {
            "codigo": "LACTEOS", 
            "nombre": "Lácteos y Derivados",
            "descripcion": "Proveedores de leche, quesos, yogurt y productos lácteos",
            "activo": True
        },
        {
            "codigo": "PANADERIA",
            "nombre": "Panadería e Insumos",
            "descripcion": "Proveedores de harinas, levaduras e insumos de panadería",
            "activo": True
        },
        {
            "codigo": "VERDURAS",
            "nombre": "Verduras y Frutas",
            "descripcion": "Proveedores de productos frescos, verduras y frutas",
            "activo": True
        },
        {
            "codigo": "ABARROTES",
            "nombre": "Abarrotes Generales",
            "descripcion": "Proveedores de productos envasados, conservas y abarrotes",
            "activo": True
        },
        {
            "codigo": "BEBIDAS",
            "nombre": "Bebidas",
            "descripcion": "Proveedores de bebidas, gaseosas, jugos y líquidos",
            "activo": True
        }
    ]
    
    print("🔄 Insertando tipos de proveedor...")
    
    for tipo_data in tipos_proveedor:
        tipo = TipoProveedor(**tipo_data)
        db.add(tipo)
        print(f"   ➕ {tipo_data['codigo']}: {tipo_data['nombre']}")
    
    try:
        db.commit()
        print("✅ Tipos de proveedor insertados correctamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar tipos de proveedor: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_tipos_proveedor()