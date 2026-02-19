"""
Script para importar datos iniciales de un nuevo tenant mediante archivos CSV.

Archivos CSV requeridos:
1. tenant_config.csv - Configuración del tenant
2. locales.csv - Locales (WEB + físicos)
3. productos.csv - Catálogo de productos
4. precios.csv - Precios por local
5. inventario.csv - Stock inicial por local
6. usuarios.csv - Usuarios administradores

Uso:
    python scripts/import_tenant_csv.py --folder ./tenant_data/
"""

import csv
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from database.database import SessionLocal
from database.models import (
    Tenant, ConfiguracionLanding, Local, Producto, 
    Inventario, Precio, User
)
from utils.security import get_password_hash


def leer_csv(filepath: str) -> list[dict]:
    """Lee un archivo CSV y retorna lista de diccionarios."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def importar_tenant_config(db: Session, data: list[dict]) -> Tenant:
    """Importa configuración del tenant."""
    if not data:
        raise ValueError("tenant_config.csv está vacío")
    
    row = data[0]
    
    # Crear tenant
    tenant = Tenant(
        codigo=row['codigo'].upper(),
        nombre=row['nombre'],
        dominio_principal=row['dominio_principal'],
        subdomain=row.get('subdomain') or row['codigo'].lower(),
        activo=True
    )
    db.add(tenant)
    db.flush()
    
    # Crear configuración landing
    colores = {
        "primario": row.get('color_primario', '#3b82f6'),
        "secundario": row.get('color_secundario', '#1e40af'),
        "acento": row.get('color_acento', '#60a5fa')
    }
    
    config = ConfiguracionLanding(
        tenant_id=tenant.id,
        nombre_comercial=row['nombre_comercial'],
        logo_url=row.get('logo_url', '/images/logo-default.png'),
        favicon_url=row.get('favicon_url', '/images/favicon.png'),
        colores=colores,
        hero_titulo=row.get('hero_titulo', f'Bienvenido a {row["nombre_comercial"]}'),
        hero_subtitulo=row.get('hero_subtitulo', 'Productos de calidad'),
        telefono=row.get('telefono'),
        email=row.get('email'),
        direccion=row.get('direccion')
    )
    db.add(config)
    
    print(f"✅ Tenant creado: {tenant.nombre} (ID: {tenant.id})")
    return tenant


def importar_locales(db: Session, tenant_id: int, data: list[dict]) -> dict:
    """Importa locales del tenant."""
    locales_map = {}
    
    for row in data:
        local = Local(
            tenant_id=tenant_id,
            codigo=row['codigo'].upper(),
            nombre=row['nombre'],
            direccion=row.get('direccion', ''),
            activo=True
        )
        db.add(local)
        db.flush()
        locales_map[row['codigo'].upper()] = local.id
        print(f"✅ Local creado: {local.nombre} (Código: {local.codigo})")
    
    return locales_map


def importar_productos(db: Session, tenant_id: int, data: list[dict]) -> dict:
    """Importa productos del tenant."""
    productos_map = {}
    
    for row in data:
        producto = Producto(
            tenant_id=tenant_id,
            sku=row['sku'].upper(),
            nombre=row['nombre'],
            descripcion=row.get('descripcion', ''),
            categoria_id=int(row['categoria_id']),
            tipo_producto_id=int(row['tipo_producto_id']),
            unidad_medida_id=int(row['unidad_medida_id']),
            precio_compra=float(row['precio_compra']) if row.get('precio_compra') else None,
            costo_fabricacion=float(row['costo_fabricacion']) if row.get('costo_fabricacion') else None,
            stock_minimo=int(row.get('stock_minimo', 0)),
            stock_critico=int(row.get('stock_critico', 0)),
            es_vendible=row.get('es_vendible', 'true').lower() == 'true',
            es_vendible_web=row.get('es_vendible_web', 'true').lower() == 'true',
            es_ingrediente=row.get('es_ingrediente', 'false').lower() == 'true',
            activo=True
        )
        db.add(producto)
        db.flush()
        productos_map[row['sku'].upper()] = producto.id
        print(f"✅ Producto creado: {producto.nombre} (SKU: {producto.sku})")
    
    return productos_map


def importar_precios(db: Session, data: list[dict], productos_map: dict, locales_map: dict):
    """Importa precios de productos por local."""
    for row in data:
        sku = row['sku'].upper()
        codigo_local = row['codigo_local'].upper()
        
        if sku not in productos_map:
            print(f"⚠️ Producto {sku} no encontrado, saltando precio")
            continue
        
        if codigo_local not in locales_map:
            print(f"⚠️ Local {codigo_local} no encontrado, saltando precio")
            continue
        
        precio = Precio(
            producto_id=productos_map[sku],
            local_id=locales_map[codigo_local],
            monto_precio=int(float(row['precio']))
        )
        db.add(precio)
    
    print(f"✅ {len(data)} precios importados")


def importar_inventario(db: Session, data: list[dict], productos_map: dict, locales_map: dict):
    """Importa stock inicial de productos por local."""
    for row in data:
        sku = row['sku'].upper()
        codigo_local = row['codigo_local'].upper()
        
        if sku not in productos_map:
            print(f"⚠️ Producto {sku} no encontrado, saltando inventario")
            continue
        
        if codigo_local not in locales_map:
            print(f"⚠️ Local {codigo_local} no encontrado, saltando inventario")
            continue
        
        inventario = Inventario(
            producto_id=productos_map[sku],
            local_id=locales_map[codigo_local],
            cantidad_stock=int(float(row['stock']))
        )
        db.add(inventario)
    
    print(f"✅ {len(data)} registros de inventario importados")


def importar_usuarios(db: Session, tenant_id: int, data: list[dict], locales_map: dict):
    """Importa usuarios del tenant."""
    for row in data:
        codigo_local = row.get('local_defecto_codigo', '').upper()
        local_defecto_id = locales_map.get(codigo_local)
        
        user = User(
            tenant_id=tenant_id,
            email=row['email'],
            nombre_completo=row['nombre_completo'],
            hashed_password=get_password_hash(row['password']),
            role_id=int(row.get('role_id', 1)),  # 1 = admin
            local_defecto_id=local_defecto_id,
            is_active=True
        )
        db.add(user)
        print(f"✅ Usuario creado: {user.email}")


def actualizar_secuencias(db: Session):
    """
    Actualiza todas las secuencias de PostgreSQL para evitar conflictos de IDs.
    """
    tablas_con_secuencia = [
        'tenants',
        'locales',
        'productos',
        'users',
        'clientes',
        'pedidos'
    ]
    
    for tabla in tablas_con_secuencia:
        try:
            db.execute(text(f"""
                SELECT setval('{tabla}_id_seq', 
                    COALESCE((SELECT MAX(id) FROM {tabla}), 1), 
                    true
                );
            """))
            print(f"✅ Secuencia de {tabla} actualizada")
        except Exception as e:
            print(f"⚠️ No se pudo actualizar secuencia de {tabla}: {e}")
    
    db.commit()


def importar_tenant_completo(folder_path: str):
    """
    Importa todos los datos de un tenant desde archivos CSV.
    
    Args:
        folder_path: Ruta a la carpeta con los archivos CSV
    """
    db = SessionLocal()
    
    try:
        # Actualizar secuencias antes de empezar
        print("\n🔧 Actualizando secuencias de base de datos...")
        actualizar_secuencias(db)
        folder = Path(folder_path)
        
        # 1. Tenant y configuración
        print("\n📋 Importando configuración del tenant...")
        tenant_data = leer_csv(folder / "tenant_config.csv")
        tenant = importar_tenant_config(db, tenant_data)
        
        # 2. Locales
        print("\n🏪 Importando locales...")
        locales_data = leer_csv(folder / "locales.csv")
        locales_map = importar_locales(db, tenant.id, locales_data)
        
        # Validar que existe local WEB
        if 'WEB' not in locales_map:
            raise ValueError("❌ ERROR: Debe existir un local con código 'WEB'")
        
        # 3. Productos
        print("\n📦 Importando productos...")
        productos_data = leer_csv(folder / "productos.csv")
        productos_map = importar_productos(db, tenant.id, productos_data)
        
        # 4. Precios
        print("\n💰 Importando precios...")
        precios_data = leer_csv(folder / "precios.csv")
        importar_precios(db, precios_data, productos_map, locales_map)
        
        # 5. Inventario
        print("\n📊 Importando inventario...")
        inventario_data = leer_csv(folder / "inventario.csv")
        importar_inventario(db, inventario_data, productos_map, locales_map)
        
        # 6. Usuarios
        print("\n👤 Importando usuarios...")
        usuarios_data = leer_csv(folder / "usuarios.csv")
        importar_usuarios(db, tenant.id, usuarios_data, locales_map)
        
        # Commit final
        db.commit()
        
        print("\n" + "="*60)
        print("✅ ¡IMPORTACIÓN COMPLETADA EXITOSAMENTE!")
        print("="*60)
        print(f"Tenant: {tenant.nombre}")
        print(f"Dominio: {tenant.dominio_principal}")
        print(f"Locales: {len(locales_map)}")
        print(f"Productos: {len(productos_map)}")
        print(f"Usuarios: {len(usuarios_data)}")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Importar datos de nuevo tenant desde CSVs')
    parser.add_argument('--folder', required=True, help='Carpeta con los archivos CSV')
    
    args = parser.parse_args()
    
    importar_tenant_completo(args.folder)
