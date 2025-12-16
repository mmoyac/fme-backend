from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import MenuItem, role_menu_permissions
from database.database import Base
import os

# Ajustar URL según entorno. Asumo local dev.
DATABASE_URL = "postgresql://fme:fme@localhost:5432/fme_database"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_menu():
    db = SessionLocal()
    try:
        print("🔍 Buscando items de menú a eliminar...")
        # Items a eliminar por href
        hrefs_to_remove = ["/admin/transferencias", "/admin/historial"]
        
        items = db.query(MenuItem).filter(MenuItem.href.in_(hrefs_to_remove)).all()
        
        if not items:
            print("✅ No se encontraron items para eliminar.")
        
        for item in items:
            print(f"🗑️ Eliminando item: {item.nombre} ({item.href})")
            # Al eliminar el item, la relación role_menu_permissions debería actualizarse si hay cascade,
            # o SQLAlchemy lo maneja.
            # Verificamos cascade en models.py:
            # role_menu_permissions tabla intermedia tiene ondelete="CASCADE" en FKs.
            db.delete(item)
            
        # Asegurar que Inventario existe
        inv = db.query(MenuItem).filter(MenuItem.href == "/admin/inventario").first()
        if inv:
            print(f"✅ Item Inventario existe: {inv.nombre}")
        else:
            print("⚠️ Item Inventario no encontrado!")

        db.commit()
        print("🚀 Actualización de menú completada.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_menu()
