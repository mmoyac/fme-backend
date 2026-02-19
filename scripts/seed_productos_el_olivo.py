"""
Script para crear productos de ejemplo para el tenant El Olivo.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Producto, Local, Precio, Inventario, Tenant, CategoriaProducto, TipoProducto, UnidadMedida

def seed_productos_el_olivo():
    db: Session = SessionLocal()
    
    try:
        # 1. Verificar que existe el tenant El Olivo
        tenant_olivo = db.query(Tenant).filter(Tenant.codigo == 'el-olivo').first()
        if not tenant_olivo:
            print("❌ Error: Tenant El Olivo no encontrado")
            return
        
        print(f"✅ Tenant encontrado: {tenant_olivo.nombre} (ID: {tenant_olivo.id})")
        
        # 2. Verificar que existe el local WEB para El Olivo
        local_web_olivo = db.query(Local).filter(
            Local.codigo == 'WEB',
            Local.tenant_id == tenant_olivo.id
        ).first()
        
        if not local_web_olivo:
            # Crear local WEB para El Olivo
            local_web_olivo = Local(
                codigo='WEB',
                nombre='Tienda Online - El Olivo',
                direccion='www.elolivo.cl',
                activo=True,
                tenant_id=tenant_olivo.id
            )
            db.add(local_web_olivo)
            db.commit()
            db.refresh(local_web_olivo)
            print(f"✅ Local WEB creado: {local_web_olivo.nombre} (ID: {local_web_olivo.id})")
        else:
            print(f"✅ Local WEB encontrado: {local_web_olivo.nombre} (ID: {local_web_olivo.id})")
        
        # 3. Obtener categoría de productos
        categoria = db.query(CategoriaProducto).filter(
            CategoriaProducto.codigo == 'PANADERIA'
        ).first()
        
        if not categoria:
            print("⚠️ Categoría PANADERIA no encontrada, usando la primera disponible")
            categoria = db.query(CategoriaProducto).first()
        
        # Obtener tipos de producto y unidad de medida
        tipo_prod_default = db.query(TipoProducto).filter(
            TipoProducto.codigo == 'ELABORADO'
        ).first()
        
        if not tipo_prod_default:
            tipo_prod_default = db.query(TipoProducto).first()
        
        unidad_default = db.query(UnidadMedida).filter(
            UnidadMedida.codigo == 'UN'
        ).first()
        
        if not unidad_default:
            unidad_default = db.query(UnidadMedida).first()
        
        # 4. Crear productos de aceite de oliva
        productos_olivo = [
            {
                "nombre": "Aceite de Oliva Extra Virgen 500ml",
                "sku": "OLIVA-EV-500",
                "descripcion": "Aceite de oliva extra virgen de primera prensada en frío",
                "precio": 8500,
                "stock": 50,
                "imagen_url": None
            },
            {
                "nombre": "Aceite de Oliva Extra Virgen 1L",
                "sku": "OLIVA-EV-1000",
                "descripcion": "Aceite de oliva extra virgen premium en botella de 1 litro",
                "precio": 15000,
                "stock": 30,
                "imagen_url": None
            },
            {
                "nombre": "Aceite de Oliva Orgánico 500ml",
                "sku": "OLIVA-ORG-500",
                "descripcion": "Aceite de oliva orgánico certificado",
                "precio": 12000,
                "stock": 25,
                "imagen_url": None
            },
            {
                "nombre": "Aceite de Oliva Blend 1L",
                "sku": "OLIVA-BL-1000",
                "descripcion": "Mezcla equilibrada de aceites de oliva",
                "precio": 7500,
                "stock": 40,
                "imagen_url": None
            },
            {
                "nombre": "Set Regalo Aceites Premium",
                "sku": "OLIVA-SET-GIFT",
                "descripcion": "Set de 3 botellas de aceites premium en caja de regalo",
                "precio": 35000,
                "stock": 15,
                "imagen_url": None
            }
        ]
        
        print("\n🌿 Creando productos de El Olivo...")
        
        for prod_data in productos_olivo:
            # Verificar si ya existe
            existe = db.query(Producto).filter(
                Producto.sku == prod_data["sku"],
                Producto.tenant_id == tenant_olivo.id
            ).first()
            
            if existe:
                print(f"⏭️ Producto ya existe: {prod_data['nombre']}")
                continue
            
            # Crear producto
            producto = Producto(
                nombre=prod_data["nombre"],
                sku=prod_data["sku"],
                descripcion=prod_data["descripcion"],
                categoria_id=categoria.id if categoria else None,
                tipo_producto_id=tipo_prod_default.id if tipo_prod_default else None,
                unidad_medida_id=unidad_default.id if unidad_default else None,
                imagen_url=prod_data["imagen_url"],
                es_vendible=True,
                es_vendible_web=True,
                activo=True,
                tenant_id=tenant_olivo.id
            )
            db.add(producto)
            db.flush()
            
            # Crear precio en local WEB
            precio = Precio(
                producto_id=producto.id,
                local_id=local_web_olivo.id,
                monto_precio=prod_data["precio"]
            )
            db.add(precio)
            
            # Crear inventario en local WEB
            inventario = Inventario(
                producto_id=producto.id,
                local_id=local_web_olivo.id,
                cantidad_stock=prod_data["stock"]
            )
            db.add(inventario)
            
            print(f"✅ Producto creado: {producto.nombre} (${prod_data['precio']:,}) - Stock: {prod_data['stock']}")
        
        db.commit()
        print(f"\n✅ Total de productos creados/verificados para El Olivo")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_productos_el_olivo()
