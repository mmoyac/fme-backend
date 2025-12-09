"""
Script para descargar imágenes de productos y almacenarlas localmente.
"""
import sys
import os
import requests
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Producto


# Directorio donde se guardarán las imágenes
IMAGES_DIR = Path(__file__).parent.parent / "static" / "productos"


def descargar_imagen(url: str, filename: str) -> bool:
    """
    Descarga una imagen desde una URL y la guarda localmente.
    
    Args:
        url: URL de la imagen
        filename: Nombre del archivo a guardar
        
    Returns:
        True si se descargó correctamente, False en caso contrario
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filepath = IMAGES_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"  ❌ Error descargando {url}: {e}")
        return False


def descargar_y_actualizar_imagenes():
    """Descarga las imágenes y actualiza las URLs en la base de datos."""
    
    # Crear directorio si no existe
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de imágenes: {IMAGES_DIR}\n")
    
    db: Session = SessionLocal()
    
    try:
        productos = db.query(Producto).all()
        
        if not productos:
            print("❌ No se encontraron productos en la base de datos")
            return
        
        print(f"📦 Encontrados {len(productos)} productos")
        print("⬇️  Descargando imágenes...\n")
        
        # Mapeo de URLs únicas para evitar descargas duplicadas
        imagenes_descargadas = {}
        actualizados = 0
        
        for producto in productos:
            if not producto.imagen_url:
                print(f"⚠️  {producto.nombre:30} - Sin imagen configurada")
                continue
            
            # Usar el SKU como nombre de archivo
            extension = "jpg"
            filename = f"{producto.sku}.{extension}"
            
            # Si ya descargamos esta URL, reutilizamos el archivo
            if producto.imagen_url in imagenes_descargadas:
                filename = imagenes_descargadas[producto.imagen_url]
                print(f"♻️  {producto.nombre:30} → {filename} (reutilizada)")
            else:
                # Descargar la imagen
                if descargar_imagen(producto.imagen_url, filename):
                    imagenes_descargadas[producto.imagen_url] = filename
                    print(f"✅ {producto.nombre:30} → {filename}")
                else:
                    print(f"⚠️  {producto.nombre:30} - Error al descargar")
                    continue
            
            # Actualizar la URL en la base de datos
            # La URL local será relativa para el frontend
            producto.imagen_url = f"/productos/{filename}"
            actualizados += 1
        
        db.commit()
        print(f"\n✨ {actualizados} productos actualizados con imágenes locales!")
        print(f"📂 Imágenes guardadas en: {IMAGES_DIR}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("📥 Descargador de Imágenes de Productos")
    print("=" * 80)
    descargar_y_actualizar_imagenes()
