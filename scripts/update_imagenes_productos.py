"""
Script para actualizar las URLs de imágenes de productos.
Asigna imágenes apropiadas según el tipo de producto.
"""
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal, engine
from database.models import Producto


# Mapeo de imágenes de Unsplash/Pexels para productos de masa y sopaipillas
IMAGENES_POR_TIPO = {
    # Masas congeladas de empanadas
    "congeladas": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&q=80",  # Discos de masa
    
    # Hojas de masa
    "hoja": "https://images.unsplash.com/photo-1574085733277-851d9d856a3a?w=800&q=80",  # Masa extendida
    
    # Masas para empanadas (redondas)
    "masas": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&q=80",  # Discos de masa
    
    # Sopaipillas
    "sopaipillas": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087?w=800&q=80",  # Sopaipillas chilenas
}


def get_imagen_url(nombre_producto: str) -> str:
    """
    Determina la URL de imagen apropiada según el nombre del producto.
    
    Args:
        nombre_producto: Nombre del producto
        
    Returns:
        URL de la imagen correspondiente
    """
    nombre_lower = nombre_producto.lower()
    
    if "sopaipilla" in nombre_lower:
        return IMAGENES_POR_TIPO["sopaipillas"]
    elif "hoja" in nombre_lower:
        return IMAGENES_POR_TIPO["hoja"]
    elif "congelada" in nombre_lower:
        return IMAGENES_POR_TIPO["congeladas"]
    elif "masa" in nombre_lower:
        return IMAGENES_POR_TIPO["masas"]
    else:
        # Imagen por defecto
        return IMAGENES_POR_TIPO["masas"]


def actualizar_imagenes():
    """Actualiza las URLs de imágenes de todos los productos."""
    db: Session = SessionLocal()
    
    try:
        productos = db.query(Producto).all()
        
        if not productos:
            print("❌ No se encontraron productos en la base de datos")
            return
        
        print(f"📦 Encontrados {len(productos)} productos")
        print("🖼️  Actualizando imágenes...\n")
        
        actualizados = 0
        for producto in productos:
            imagen_url = get_imagen_url(producto.nombre)
            producto.imagen_url = imagen_url
            
            print(f"✅ {producto.nombre:30} → {imagen_url[:60]}...")
            actualizados += 1
        
        db.commit()
        print(f"\n✨ {actualizados} productos actualizados con éxito!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("🎨 Actualizador de Imágenes de Productos")
    print("=" * 80)
    actualizar_imagenes()
