"""
Script para poblar los sellos de advertencia chilenos en la base de datos.
"""
import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import SelloAdvertencia

def seed_sellos():
    db = SessionLocal()
    
    try:
        # Verificar si ya existen sellos
        existe = db.query(SelloAdvertencia).first()
        if existe:
            print("⚠️  Ya existen sellos en la base de datos. Abortando...")
            return
        
        sellos = [
            {
                "codigo": "ALTO_CALORIAS",
                "nombre": "Alto en Calorías",
                "descripcion": "Producto con alto contenido energético (≥350 kcal/100g o ≥100 kcal/100ml)",
                "color": "#000000",  # Negro (octágono)
                "icono": "🔴",
                "orden": 1,
                "activo": True
            },
            {
                "codigo": "ALTO_AZUCARES",
                "nombre": "Alto en Azúcares",
                "descripcion": "Producto con alto contenido de azúcares (≥15g/100g o ≥6g/100ml)",
                "color": "#000000",
                "icono": "🔴",
                "orden": 2,
                "activo": True
            },
            {
                "codigo": "ALTO_SODIO",
                "nombre": "Alto en Sodio",
                "descripcion": "Producto con alto contenido de sodio (≥800mg/100g o ≥100mg/100ml)",
                "color": "#000000",
                "icono": "🔴",
                "orden": 3,
                "activo": True
            },
            {
                "codigo": "ALTO_GRASAS_SAT",
                "nombre": "Alto en Grasas Saturadas",
                "descripcion": "Producto con alto contenido de grasas saturadas (≥6g/100g o ≥3g/100ml)",
                "color": "#000000",
                "icono": "🔴",
                "orden": 4,
                "activo": True
            },
            {
                "codigo": "CONTIENE_EDULCORANTES",
                "nombre": "Contiene Edulcorantes",
                "descripcion": "Producto que contiene edulcorantes (no calóricos o naturales)",
                "color": "#000000",
                "icono": "⚫",
                "orden": 5,
                "activo": True
            },
            {
                "codigo": "CONTIENE_CAFEINA",
                "nombre": "Contiene Cafeína",
                "descripcion": "Producto que contiene cafeína, no recomendado para niños",
                "color": "#000000",
                "icono": "⚫",
                "orden": 6,
                "activo": True
            }
        ]
        
        for sello_data in sellos:
            sello = SelloAdvertencia(**sello_data)
            db.add(sello)
            print(f"✓ Creado sello: {sello_data['nombre']}")
        
        db.commit()
        print(f"\n✅ {len(sellos)} sellos de advertencia creados exitosamente")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🏷️  Poblando sellos de advertencia chilenos...\n")
    seed_sellos()
