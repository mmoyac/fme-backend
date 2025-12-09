"""
Script para cargar locales desde CSV a la base de datos.
"""
import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Local


def load_locales_from_csv(db: Session, csv_path: str) -> int:
    """
    Carga locales desde un archivo CSV a la base de datos.
    """
    locales_cargados = 0
    locales_omitidos = 0
    
    print(f"📂 Leyendo archivo: {csv_path}\n")
    
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                
                for row in csv_reader:
                    # Saltar filas sin nombre
                    if not row.get('nombre') or not row['nombre'].strip():
                        continue
                    
                    nombre = row['nombre'].strip()
                    direccion = row['direccion'].strip() if row.get('direccion') else None
                    
                    # Verificar si el nombre ya existe (campo único)
                    existing = db.query(Local).filter(Local.nombre == nombre).first()
                    if existing:
                        print(f"⚠️  Local '{nombre}' ya existe - Omitiendo")
                        locales_omitidos += 1
                        continue
                    
                    # Crear instancia del modelo Local
                    local = Local(
                        nombre=nombre,
                        direccion=direccion
                    )
                    
                    db.add(local)
                    locales_cargados += 1
                    print(f"✅ Local agregado: {nombre}")
            
            # Si llegamos aquí, el encoding funcionó
            break
            
        except UnicodeDecodeError:
            if encoding == encodings[-1]:
                raise
            continue
    
    # Commit de todas las inserciones
    db.commit()
    
    print(f"\n{'='*60}")
    print(f"📊 Resumen de carga:")
    print(f"   • Locales cargados: {locales_cargados}")
    print(f"   • Locales omitidos: {locales_omitidos}")
    print(f"{'='*60}\n")
    
    return locales_cargados


def main():
    """Función principal del script."""
    print("\n🚀 Iniciando carga de locales...\n")
    
    # Ruta al archivo CSV
    csv_path = Path("docs/Locales.csv")
    
    # Validar que el archivo existe
    if not csv_path.exists():
        print(f"❌ Error: Archivo '{csv_path}' no encontrado")
        sys.exit(1)
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        locales_cargados = load_locales_from_csv(db, str(csv_path))
        
        if locales_cargados > 0:
            print("✅ Carga completada exitosamente!")
        else:
            print("⚠️  No se cargaron nuevos locales")
            
    except Exception as e:
        print(f"\n❌ Error durante la carga: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
