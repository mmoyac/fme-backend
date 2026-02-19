"""
Script para eliminar el menú de Caja del sistema.
La funcionalidad de caja se accede ahora desde /admin/pedidos/pos

Ejecutar: docker-compose exec backend python scripts/eliminar_menu_caja.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models import MenuItem, Role
from sqlalchemy import delete

def eliminar_menu_caja():
    """Elimina el item de menú 'Caja' del sistema."""
    db = SessionLocal()
    
    try:
        # Buscar el menu item de Caja
        caja_item = db.query(MenuItem).filter(MenuItem.nombre == "Caja").first()
        
        if not caja_item:
            print("ℹ️  El menú 'Caja' no existe en la base de datos")
            return
        
        print(f"🔍 Menú encontrado: {caja_item.nombre} (ID: {caja_item.id})")
        print(f"   - Href: {caja_item.href}")
        print(f"   - Icon: {caja_item.icon}")
        print(f"   - Orden: {caja_item.orden}")
        
        # Las relaciones con roles se eliminan automáticamente con CASCADE
        # gracias a la configuración del modelo MenuItem
        
        # Eliminar el menu item
        db.delete(caja_item)
        db.commit()
        
        print(f"\n✅ Menú 'Caja' eliminado exitosamente")
        print(f"   La funcionalidad de caja ahora está en: /admin/pedidos/pos")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al eliminar menú: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️  Eliminando menú 'Caja' del sistema...\n")
    eliminar_menu_caja()
    print("\n✅ Proceso completado")
