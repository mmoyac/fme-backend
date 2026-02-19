from database.database import SessionLocal
from database.models import MenuItem

db = SessionLocal()

# Buscar todos los items de menú
items = db.query(MenuItem).order_by(MenuItem.orden).all()

print("=" * 70)
print("ITEMS DE MENÚ")
print("=" * 70)

for item in items:
    print(f"ID: {item.id:3d} | Orden: {item.orden:2d} | Nombre: {item.nombre:20s} | Ruta: {item.href}")

# Buscar específicamente items con "despacho" en el nombre o ruta
print("\n" + "=" * 70)
print("ITEMS RELACIONADOS CON DESPACHO")
print("=" * 70)

despacho_items = [i for i in items if 'despacho' in i.nombre.lower() or 'despacho' in i.href.lower()]

if despacho_items:
    for item in despacho_items:
        print(f"ID: {item.id} | Nombre: {item.nombre} | Ruta: {item.href}")
else:
    print("No se encontraron items de despacho")

db.close()
