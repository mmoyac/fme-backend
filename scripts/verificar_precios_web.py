"""
Script para verificar precios en el local WEB
"""
import sys
sys.path.append(".")

from database.database import SessionLocal
from database.models import Producto, Precio, Local
from sqlalchemy.orm import joinedload

def main():
    db = SessionLocal()
    try:
        # Buscar local WEB
        local_web = db.query(Local).filter(Local.codigo == 'WEB').first()
        if not local_web:
            print("❌ Local WEB no encontrado")
            return
        
        print(f"✅ Local WEB encontrado: ID={local_web.id}, Nombre={local_web.nombre}")
        print()
        
        # Buscar productos que NO tienen precio en WEB
        productos_sin_precio = db.query(Producto).outerjoin(
            Precio, 
            (Precio.producto_id == Producto.id) & (Precio.local_id == local_web.id)
        ).filter(
            Precio.id == None
        ).all()
        
        if productos_sin_precio:
            print(f"⚠️ Productos SIN precio en local WEB ({len(productos_sin_precio)}):")
            for p in productos_sin_precio:
                print(f"   - ID: {p.id}, SKU: {p.sku}, Nombre: {p.nombre}")
        else:
            print("✅ Todos los productos tienen precio en local WEB")
        
        print()
        
        # Buscar el producto específico
        aceite = db.query(Producto).filter(Producto.nombre.ilike('%Aceite de Oliva%')).first()
        if aceite:
            print(f"🔍 Producto encontrado:")
            print(f"   ID: {aceite.id}")
            print(f"   SKU: {aceite.sku}")
            print(f"   Nombre: {aceite.nombre}")
            
            # Verificar precio
            precio_web = db.query(Precio).filter(
                Precio.producto_id == aceite.id,
                Precio.local_id == local_web.id
            ).first()
            
            if precio_web:
                print(f"   ✅ Precio en WEB: ${precio_web.monto_precio:,.0f}")
            else:
                print(f"   ❌ NO tiene precio en WEB")
                
                # Ver precios en otros locales
                otros_precios = db.query(Precio).options(
                    joinedload(Precio.local)
                ).filter(
                    Precio.producto_id == aceite.id
                ).all()
                
                if otros_precios:
                    print(f"   📍 Precios en otros locales:")
                    for p in otros_precios:
                        print(f"      - {p.local.nombre}: ${p.monto_precio:,.0f}")
                else:
                    print(f"   ⚠️ No tiene precio en ningún local")
        else:
            print("❌ Producto 'Aceite de Oliva' no encontrado")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
