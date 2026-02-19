"""
Script para asignar precios al local WEB desde otros locales
"""
import sys
sys.path.append(".")

from database.database import SessionLocal
from database.models import Producto, Precio, Local

def main():
    db = SessionLocal()
    try:
        # Buscar local WEB
        local_web = db.query(Local).filter(Local.codigo == 'WEB').first()
        if not local_web:
            print("❌ Local WEB no encontrado")
            return
        
        print(f"✅ Local WEB: ID={local_web.id}, Nombre={local_web.nombre}")
        print()
        
        # Buscar productos que NO tienen precio en WEB
        productos_sin_precio = db.query(Producto).outerjoin(
            Precio, 
            (Precio.producto_id == Producto.id) & (Precio.local_id == local_web.id)
        ).filter(
            Precio.id == None
        ).all()
        
        if not productos_sin_precio:
            print("✅ Todos los productos ya tienen precio en local WEB")
            return
        
        print(f"⚙️ Procesando {len(productos_sin_precio)} productos...")
        print()
        
        precios_creados = 0
        productos_sin_referencia = []
        
        for producto in productos_sin_precio:
            # Buscar precio en cualquier otro local
            precio_referencia = db.query(Precio).filter(
                Precio.producto_id == producto.id
            ).first()
            
            if precio_referencia:
                # Crear precio en local WEB
                nuevo_precio = Precio(
                    producto_id=producto.id,
                    local_id=local_web.id,
                    monto_precio=precio_referencia.monto_precio,
                    tenant_id=local_web.tenant_id
                )
                db.add(nuevo_precio)
                precios_creados += 1
                print(f"✅ {producto.sku} - {producto.nombre}: ${precio_referencia.monto_precio:,.0f}")
            else:
                productos_sin_referencia.append(producto)
                print(f"⚠️ {producto.sku} - {producto.nombre}: No tiene precio en ningún local")
        
        # Commit de los cambios
        if precios_creados > 0:
            db.commit()
            print()
            print(f"✅ Se crearon {precios_creados} precios en el local WEB")
        
        if productos_sin_referencia:
            print()
            print(f"⚠️ {len(productos_sin_referencia)} productos sin precio de referencia:")
            for p in productos_sin_referencia:
                print(f"   - {p.sku}: {p.nombre}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
