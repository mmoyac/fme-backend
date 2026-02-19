"""
Script para poblar la tabla unidades_medida con valores comunes.
Ejecutar: python scripts/seed_unidades_medida.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import UnidadMedida

def seed_unidades_medida():
    db: Session = SessionLocal()
    
    # Verificar si ya existen unidades
    existing = db.query(UnidadMedida).count()
    if existing > 0:
        print(f"Ya existen {existing} unidades de medida. Saltando...")
        db.close()
        return
    
    unidades = [
        # Unidades de cantidad
        {
            "codigo": "UN",
            "nombre": "Unidad",
            "simbolo": "un",
            "tipo": "CANTIDAD",
            "factor_conversion": 1.0,
            "activo": True
        },
        {
            "codigo": "MEDIA_DOC",
            "nombre": "Media Docena",
            "simbolo": "1/2 doc",
            "tipo": "CANTIDAD",
            "factor_conversion": 6.0,
            "unidad_base_id": None,  # Se actualizará después
            "activo": True
        },
        {
            "codigo": "DOC",
            "nombre": "Docena",
            "simbolo": "doc",
            "tipo": "CANTIDAD",
            "factor_conversion": 12.0,
            "unidad_base_id": None,  # Se actualizará después
            "activo": True
        },
        {
            "codigo": "CAJA",
            "nombre": "Caja",
            "simbolo": "caja",
            "tipo": "CANTIDAD",
            "factor_conversion": None,
            "activo": True
        },
        {
            "codigo": "PACK",
            "nombre": "Pack",
            "simbolo": "pack",
            "tipo": "CANTIDAD",
            "factor_conversion": None,
            "activo": True
        },
        # Unidades de peso
        {
            "codigo": "KG",
            "nombre": "Kilogramo",
            "simbolo": "kg",
            "tipo": "PESO",
            "factor_conversion": 1.0,
            "activo": True
        },
        {
            "codigo": "GR",
            "nombre": "Gramo",
            "simbolo": "gr",
            "tipo": "PESO",
            "factor_conversion": 0.001,
            "unidad_base_id": None,  # Se actualizará después
            "activo": True
        },
        # Unidades de volumen
        {
            "codigo": "LT",
            "nombre": "Litro",
            "simbolo": "lt",
            "tipo": "VOLUMEN",
            "factor_conversion": 1.0,
            "activo": True
        },
        {
            "codigo": "ML",
            "nombre": "Mililitro",
            "simbolo": "ml",
            "tipo": "VOLUMEN",
            "factor_conversion": 0.001,
            "unidad_base_id": None,  # Se actualizará después
            "activo": True
        }
    ]
    
    print("🌱 Poblando tabla unidades_medida...")
    
    unidades_creadas = {}
    
    # Primera pasada: crear todas las unidades
    for unidad_data in unidades:
        unidad = UnidadMedida(**unidad_data)
        db.add(unidad)
        db.flush()  # Para obtener el ID
        unidades_creadas[unidad_data["codigo"]] = unidad.id
        print(f"  ✓ Creada unidad: {unidad.nombre} ({unidad.simbolo})")
    
    # Segunda pasada: actualizar relaciones de unidad_base_id
    relaciones = {
        "MEDIA_DOC": "UN",  # Media docena se basa en unidad
        "DOC": "UN",        # Docena se basa en unidad
        "GR": "KG",         # Gramo se basa en kilogramo
        "ML": "LT"          # Mililitro se basa en litro
    }
    
    for codigo_derivado, codigo_base in relaciones.items():
        unidad = db.query(UnidadMedida).filter(
            UnidadMedida.codigo == codigo_derivado
        ).first()
        if unidad:
            unidad.unidad_base_id = unidades_creadas[codigo_base]
            print(f"  ↳ {codigo_derivado} → unidad base: {codigo_base}")
    
    db.commit()
    print(f"\n✅ Creadas {len(unidades)} unidades de medida exitosamente!")
    db.close()

if __name__ == "__main__":
    seed_unidades_medida()
