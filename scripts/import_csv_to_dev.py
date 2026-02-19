"""
Script para importar datos del cliente desde CSV a desarrollo.
Importación INCREMENTAL: agrega nuevos registros, actualiza existentes por clave única.
"""
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import SessionLocal
from database.models import Producto, Local, Proveedor, Inventario, Cliente, ConfiguracionLanding, Categoria
from sqlalchemy import func

def leer_csv(filepath: str) -> list[dict]:
    """Lee CSV y retorna lista de diccionarios."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def importar_productos(db, productos_csv: list[dict], tenant_id: int = 1):
    """Importar productos nuevos o actualizar existentes."""
    print("\n📦 Importando Productos...")
    
    creados = 0
    actualizados = 0
    errores = 0
    
    for row in productos_csv:
        try:
            sku = row['SKU'].strip().upper()
            
            # Buscar producto existente
            producto = db.query(Producto).filter(
                Producto.tenant_id == tenant_id,
                Producto.sku == sku
            ).first()
            
            # Buscar categoría
            categoria = db.query(Categoria).filter(
                Categoria.nombre == row['Categoria'].strip()
            ).first()
            
            if not categoria:
                print(f"  ⚠️  Categoría '{row['Categoria']}' no existe. Creando...")
                categoria = Categoria(
                    nombre=row['Categoria'].strip(),
                    descripcion=f"Categoría {row['Categoria']}"
                )
                db.add(categoria)
                db.flush()
            
            if producto:
                # Actualizar existente
                producto.nombre = row['Nombre'].strip()
                producto.descripcion = row.get('Descripcion', '').strip()
                producto.categoria_id = categoria.id
                producto.unidad = row.get('Unidad', 'unidad').strip()
                producto.imagen_url = row.get('Imagen URL', '').strip() or None
                
                actualizados += 1
                print(f"  ✏️  Actualizado: {sku} - {producto.nombre}")
            else:
                # Crear nuevo
                producto = Producto(
                    tenant_id=tenant_id,
                    sku=sku,
                    nombre=row['Nombre'].strip(),
                    descripcion=row.get('Descripcion', '').strip(),
                    categoria_id=categoria.id,
                    unidad=row.get('Unidad', 'unidad').strip(),
                    imagen_url=row.get('Imagen URL', '').strip() or None
                )
                db.add(producto)
                creados += 1
                print(f"  ✅ Creado: {sku} - {producto.nombre}")
            
            db.flush()
            
            # Asignar precio al local WEB
            if 'Precio Venta' in row and row['Precio Venta']:
                precio_venta = float(row['Precio Venta'])
                
                local_web = db.query(Local).filter(
                    Local.tenant_id == tenant_id,
                    Local.codigo == 'WEB'
                ).first()
                
                if local_web:
                    from database.models import Precio
                    precio = db.query(Precio).filter(
                        Precio.producto_id == producto.id,
                        Precio.local_id == local_web.id
                    ).first()
                    
                    if precio:
                        precio.monto_precio = precio_venta
                    else:
                        precio = Precio(
                            producto_id=producto.id,
                            local_id=local_web.id,
                            monto_precio=precio_venta
                        )
                        db.add(precio)
                    
                    print(f"    💰 Precio WEB: ${precio_venta:,.0f}")
        
        except Exception as e:
            print(f"  ❌ Error en {row.get('SKU', 'unknown')}: {e}")
            errores += 1
            continue
    
    db.commit()
    print(f"\n  Resumen: {creados} creados | {actualizados} actualizados | {errores} errores")

def importar_locales(db, locales_csv: list[dict], tenant_id: int = 1):
    """Importar locales/sucursales nuevas."""
    print("\n🏪 Importando Locales...")
    
    creados = 0
    actualizados = 0
    
    for row in locales_csv:
        try:
            codigo = row['Codigo'].strip().upper()
            
            # No permitir crear/actualizar local WEB
            if codigo == 'WEB':
                print(f"  ⚠️  Local WEB es del sistema, omitiendo...")
                continue
            
            local = db.query(Local).filter(
                Local.tenant_id == tenant_id,
                Local.codigo == codigo
            ).first()
            
            if local:
                # Actualizar
                local.nombre = row['Nombre'].strip()
                local.direccion = row.get('Direccion', '').strip()
                local.telefono = row.get('Telefono', '').strip()
                actualizados += 1
                print(f"  ✏️  Actualizado: {codigo} - {local.nombre}")
            else:
                # Crear
                local = Local(
                    tenant_id=tenant_id,
                    codigo=codigo,
                    nombre=row['Nombre'].strip(),
                    direccion=row.get('Direccion', '').strip(),
                    telefono=row.get('Telefono', '').strip()
                )
                db.add(local)
                creados += 1
                print(f"  ✅ Creado: {codigo} - {local.nombre}")
        
        except Exception as e:
            print(f"  ❌ Error en {row.get('Codigo', 'unknown')}: {e}")
            continue
    
    db.commit()
    print(f"\n  Resumen: {creados} creados | {actualizados} actualizados")

def importar_inventario(db, inventario_csv: list[dict], tenant_id: int = 1):
    """Importar inventario inicial (SUMAR a existente, no reemplazar)."""
    print("\n📊 Importando Inventario Inicial...")
    
    creados = 0
    actualizados = 0
    
    for row in inventario_csv:
        try:
            sku = row['SKU'].strip().upper()
            codigo_local = row['Local'].strip().upper()
            cantidad = int(row['Stock Inicial'])
            
            # Buscar producto
            producto = db.query(Producto).filter(
                Producto.tenant_id == tenant_id,
                Producto.sku == sku
            ).first()
            
            if not producto:
                print(f"  ⚠️  Producto {sku} no existe, omitiendo...")
                continue
            
            # Buscar local
            local = db.query(Local).filter(
                Local.tenant_id == tenant_id,
                Local.codigo == codigo_local
            ).first()
            
            if not local:
                print(f"  ⚠️  Local {codigo_local} no existe, omitiendo...")
                continue
            
            # Buscar inventario existente
            inv = db.query(Inventario).filter(
                Inventario.producto_id == producto.id,
                Inventario.local_id == local.id
            ).first()
            
            if inv:
                # SUMAR al stock existente
                stock_anterior = inv.cantidad_stock
                inv.cantidad_stock += cantidad
                actualizados += 1
                print(f"  ✏️  {sku} en {codigo_local}: {stock_anterior} → {inv.cantidad_stock} (+{cantidad})")
            else:
                # Crear nuevo registro
                inv = Inventario(
                    producto_id=producto.id,
                    local_id=local.id,
                    cantidad_stock=cantidad
                )
                db.add(inv)
                creados += 1
                print(f"  ✅ {sku} en {codigo_local}: {cantidad} unidades")
        
        except Exception as e:
            print(f"  ❌ Error en {row.get('SKU', 'unknown')}: {e}")
            continue
    
    db.commit()
    print(f"\n  Resumen: {creados} creados | {actualizados} actualizados")

def main():
    print("=" * 70)
    print("  IMPORTADOR DE DATOS DEL CLIENTE A DESARROLLO")
    print("=" * 70)
    
    # Archivos CSV esperados en carpeta data/
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print(f"\n❌ Carpeta {data_dir} no existe.")
        print("Crea la carpeta 'data/' y coloca los CSV del cliente ahí.")
        return
    
    db = SessionLocal()
    tenant_id = 1  # Masas Estación
    
    try:
        # 1. Productos (obligatorio)
        productos_file = data_dir / "productos.csv"
        if productos_file.exists():
            productos_data = leer_csv(productos_file)
            importar_productos(db, productos_data, tenant_id)
        else:
            print("\n⚠️  Archivo productos.csv no encontrado, omitiendo...")
        
        # 2. Locales
        locales_file = data_dir / "locales.csv"
        if locales_file.exists():
            locales_data = leer_csv(locales_file)
            importar_locales(db, locales_data, tenant_id)
        else:
            print("\n⚠️  Archivo locales.csv no encontrado, omitiendo...")
        
        # 3. Inventario
        inventario_file = data_dir / "inventario_inicial.csv"
        if inventario_file.exists():
            inventario_data = leer_csv(inventario_file)
            importar_inventario(db, inventario_data, tenant_id)
        else:
            print("\n⚠️  Archivo inventario_inicial.csv no encontrado, omitiendo...")
        
        print("\n" + "=" * 70)
        print("  ✅ IMPORTACIÓN COMPLETADA")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("1. Revisar datos en http://localhost:3001/admin/productos")
        print("2. Verificar catálogo en http://localhost:3000")
        print("3. Probar flujo de pedido completo")
        print("4. Si todo OK, exportar con: python export_tenant_data.py")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
