"""
Script para consultar tipos de producto disponibles.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import TipoProducto

def consultar_tipos():
    db: Session = SessionLocal()
    
    print("\n*** TIPOS DE PRODUCTO:")
    print("=" * 90)
    tipos = db.query(TipoProducto).all()
    if tipos:
        print(f"{'ID':<5} {'Codigo':<15} {'Nombre':<30} {'Descripcion':<35} {'Activo':<6}")
        print("-" * 90)
        for t in tipos:
            desc = str(t.descripcion)[:34] if t.descripcion else ""
            print(f"{t.id:<5} {t.codigo:<15} {t.nombre:<30} {desc:<35} {t.activo!s:<6}")
    else:
        print("*** No hay tipos de producto registrados")
    
    db.close()

if __name__ == "__main__":
    consultar_tipos()
