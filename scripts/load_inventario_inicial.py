"""
Script para cargar inventario inicial en todos los locales.
Asigna todos los productos a cada local con stock de 100 unidades.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Inventario, Producto, Local


def load_inventario_inicial(db: Session, cantidad_inicial: int = 100) -> int:
    """
    Carga inventario inicial asignando todos los productos a cada local.
    
    Args:
        db: Sesión de SQLAlchemy
        cantidad_inicial: Cantidad de stock inicial para cada producto
        
    Returns:
        Número de registros de inventario creados
    """
    registros_creados = 0
    registros_omitidos = 0
    
    print(f"📦 Generando inventario inicial con stock de {cantidad_inicial} unidades...\n")
    
    # Obtener todos los locales
    locales = db.query(Local).all()
    print(f"🏢 Locales encontrados: {len(locales)}")
    for local in locales:
        print(f"   • {local.nombre}")
    
    # Obtener todos los productos
    productos = db.query(Producto).all()
    print(f"\n📦 Productos encontrados: {len(productos)}")
    
    print(f"\n{'='*60}")
    print("Creando registros de inventario...")
    print(f"{'='*60}\n")
    
    # Para cada local, crear inventario de todos los productos
    for local in locales:
        print(f"\n🏢 Local: {local.nombre}")
        productos_agregados = 0
        
        for producto in productos:
            # Verificar si ya existe inventario para este producto-local
            existing = db.query(Inventario).filter(
                Inventario.producto_id == producto.id,
                Inventario.local_id == local.id
            ).first()
            
            if existing:
                registros_omitidos += 1
                continue
            
            # Crear registro de inventario
            inventario = Inventario(
                producto_id=producto.id,
                local_id=local.id,
                cantidad_stock=cantidad_inicial
            )
            
            db.add(inventario)
            registros_creados += 1
            productos_agregados += 1
        
        print(f"   ✅ {productos_agregados} productos agregados al inventario")
    
    # Commit de todas las inserciones
    db.commit()
    
    print(f"\n{'='*60}")
    print(f"📊 Resumen de carga:")
    print(f"   • Registros creados: {registros_creados}")
    print(f"   • Registros omitidos (ya existían): {registros_omitidos}")
    print(f"   • Total de locales: {len(locales)}")
    print(f"   • Total de productos: {len(productos)}")
    print(f"   • Stock inicial por producto: {cantidad_inicial} unidades")
    print(f"{'='*60}\n")
    
    return registros_creados


def main():
    """Función principal del script."""
    print("\n🚀 Iniciando carga de inventario inicial...\n")
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        registros_creados = load_inventario_inicial(db, cantidad_inicial=100)
        
        if registros_creados > 0:
            print("✅ Carga de inventario completada exitosamente!")
        else:
            print("⚠️  No se crearon nuevos registros de inventario")
            
    except Exception as e:
        print(f"\n❌ Error durante la carga: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
