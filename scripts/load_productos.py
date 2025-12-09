"""
Script para cargar productos desde CSV a la base de datos.
Sigue las convenciones definidas en AGENTS.md.
"""
import csv
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Producto


def load_productos_from_csv(db: Session, csv_path: str) -> int:
    """
    Carga productos desde un archivo CSV a la base de datos.
    
    Args:
        db: Sesión de SQLAlchemy
        csv_path: Ruta al archivo CSV
        
    Returns:
        Número de productos cargados exitosamente
    """
    productos_cargados = 0
    productos_omitidos = 0
    
    print(f"📂 Leyendo archivo: {csv_path}\n")
    
    # Intentar diferentes codificaciones
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    file_content = None
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as file:
                file_content = file.read()
                print(f"✓ Archivo leído con codificación: {encoding}\n")
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        raise Exception("No se pudo leer el archivo con ninguna codificación conocida")
    
    # Procesar el contenido
    from io import StringIO
    csv_file = StringIO(file_content)
    csv_reader = csv.DictReader(csv_file, delimiter=';')
    
    for row in csv_reader:
        # Saltar filas vacías o sin SKU
        if not row.get('sku') or not row['sku'].strip():
            continue
            
        sku = row['sku'].strip()
        nombre = row['nombre'].strip() if row.get('nombre') else f"Producto {sku}"
        descripcion = row['descripcion'].strip() if row.get('descripcion') and row['descripcion'] != ',' else None
        
        # Verificar si el SKU ya existe (campo único)
        existing = db.query(Producto).filter(Producto.sku == sku).first()
        if existing:
            print(f"⚠️  SKU '{sku}' ya existe - Omitiendo")
            productos_omitidos += 1
            continue
        
        # Crear instancia del modelo Producto
        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            sku=sku
        )
        
        db.add(producto)
        productos_cargados += 1
        print(f"✅ Producto agregado: {nombre} (SKU: {sku})")
    
    # Commit de todas las inserciones
    db.commit()
    
    print(f"\n{'='*60}")
    print(f"📊 Resumen de carga:")
    print(f"   • Productos cargados: {productos_cargados}")
    print(f"   • Productos omitidos: {productos_omitidos}")
    print(f"{'='*60}\n")
    
    return productos_cargados


def main():
    """Función principal del script."""
    print("\n🚀 Iniciando carga de productos...\n")
    
    # Ruta al archivo CSV
    csv_path = Path("docs/Productos.csv")
    
    # Validar que el archivo existe
    if not csv_path.exists():
        print(f"❌ Error: Archivo '{csv_path}' no encontrado")
        sys.exit(1)
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        productos_cargados = load_productos_from_csv(db, str(csv_path))
        
        if productos_cargados > 0:
            print("✅ Carga completada exitosamente!")
        else:
            print("⚠️  No se cargaron nuevos productos")
            
    except Exception as e:
        print(f"\n❌ Error durante la carga: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
