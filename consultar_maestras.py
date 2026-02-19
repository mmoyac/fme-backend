"""
Script para consultar categorías y unidades de medida actuales.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import CategoriaProducto, UnidadMedida

def consultar_maestras():
    db: Session = SessionLocal()
    
    print("\n*** CATEGORIAS DE PRODUCTO:")
    print("=" * 80)
    categorias = db.query(CategoriaProducto).all()
    if categorias:
        print(f"{'ID':<5} {'Codigo':<12} {'Nombre':<25} {'Descripcion':<35} {'Puntos':<8} {'Activo':<6}")
        print("-" * 80)
        for cat in categorias:
            print(f"{cat.id:<5} {cat.codigo:<12} {cat.nombre:<25} {str(cat.descripcion)[:34]:<35} {cat.puntos_fidelidad:<8} {cat.activo!s:<6}")
    else:
        print("*** No hay categorias registradas")
    
    print("\n*** UNIDADES DE MEDIDA:")
    print("=" * 100)
    unidades = db.query(UnidadMedida).all()
    if unidades:
        print(f"{'ID':<5} {'Codigo':<10} {'Nombre':<20} {'Simbolo':<10} {'Tipo':<12} {'Factor':<10} {'Base ID':<8} {'Activo':<6}")
        print("-" * 100)
        for u in unidades:
            factor = f"{u.factor_conversion:.4f}" if u.factor_conversion else "N/A"
            base = str(u.unidad_base_id) if u.unidad_base_id else "-"
            print(f"{u.id:<5} {u.codigo:<10} {u.nombre:<20} {u.simbolo:<10} {u.tipo or '':<12} {factor:<10} {base:<8} {u.activo!s:<6}")
    else:
        print("*** No hay unidades de medida registradas")
    
    db.close()

if __name__ == "__main__":
    consultar_maestras()
