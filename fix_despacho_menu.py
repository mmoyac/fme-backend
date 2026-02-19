from database.database import SessionLocal
from database.models import MenuItem

db = SessionLocal()

# Buscar el item de menú de Despacho
despacho_item = db.query(MenuItem).filter(MenuItem.id == 19).first()

if despacho_item:
    print(f"Item de menú encontrado:")
    print(f"  ID: {despacho_item.id}")
    print(f"  Nombre: {despacho_item.nombre}")
    print(f"  Ruta actual: {despacho_item.href}")
    
    # Actualizar la ruta
    despacho_item.href = "/admin/despacho"
    
    db.commit()
    db.refresh(despacho_item)
    
    print(f"\n✅ Ruta actualizada a: {despacho_item.href}")
else:
    print("❌ Item de menú de Despacho no encontrado")

db.close()
