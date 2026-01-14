#!/usr/bin/env python3
"""
Script de prueba para verificar endpoints de tipos de venta.
"""
import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import get_db
from database.models import TipoVenta, CategoriaProducto
from sqlalchemy.orm import joinedload

def test_endpoints():
    """Probar funcionalidad de tipos de venta."""
    db = next(get_db())
    
    print("🧪 Prueba de funcionalidad Tipos de Venta")
    print("==========================================")
    
    print("1. Verificar tipos de venta disponibles:")
    tipos = db.query(TipoVenta).all()
    for tipo in tipos:
        print(f"   ✅ {tipo.codigo}: {tipo.nombre}")
    
    print(f"\n2. Verificar categorías (total: {db.query(CategoriaProducto).count()}):")
    categorias = db.query(CategoriaProducto).options(joinedload(CategoriaProducto.tipo_venta)).all()
    for cat in categorias:
        tipo_info = f"→ {cat.tipo_venta.codigo}" if cat.tipo_venta else "→ Sin asignar"
        print(f"   📋 {cat.codigo}: {cat.nombre} {tipo_info}")
    
    print("\n3. Prueba de asignación (simulada):")
    print("   💡 Próximo paso: Usar el backoffice para asignar tipos de venta a categorías")
    
    db.close()

if __name__ == "__main__":
    test_endpoints()