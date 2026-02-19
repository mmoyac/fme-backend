#!/usr/bin/env python3
"""
Script para sincronizar menús RBAC de desarrollo a producción.
Ejecutar en el servidor VPS dentro del contenedor backend.
"""
import sys
import os
sys.path.append('/app')

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import MenuItem

# Menús de desarrollo (12 items)
MENUS_DEV = [
    {"nombre": "Dashboard", "href": "/admin/dashboard", "icon": "HomeIcon", "orden": 1},
    {"nombre": "Pedidos", "href": "/admin/pedidos", "icon": "ShoppingCartIcon", "orden": 2},
    {"nombre": "Productos", "href": "/admin/productos", "icon": "CubeIcon", "orden": 3},
    {"nombre": "Compras", "href": "/admin/compras", "icon": "ShoppingBagIcon", "orden": 4},
    {"nombre": "Inventario", "href": "/admin/inventario", "icon": "ArchiveBoxIcon", "orden": 5},
    {"nombre": "Precios", "href": "/admin/precios", "icon": "CurrencyDollarIcon", "orden": 6},
    {"nombre": "Clientes", "href": "/admin/clientes", "icon": "UsersIcon", "orden": 7},
    {"nombre": "Alertas", "href": "/admin/alertas", "icon": "BellIcon", "orden": 12},
    {"nombre": "Despacho", "href": "/admin/despacho", "icon": "TruckIcon", "orden": 13},
    {"nombre": "Recepción de Mercancías", "href": "/admin/recepcion", "icon": "InboxIcon", "orden": 15},
    {"nombre": "Producción", "href": "/admin/produccion", "icon": "CogIcon", "orden": 50},
    {"nombre": "Mantenedores", "href": "/admin/mantenedores", "icon": "WrenchIcon", "orden": 100},
]

def sync_menus():
    db: Session = SessionLocal()
    try:
        # 1. Obtener todos los menús actuales
        current_menus = db.query(MenuItem).all()
        print(f"\n📊 Menús actuales en BD: {len(current_menus)}")
        
        # 2. Eliminar todos los menús existentes
        print("\n🗑️  Eliminando menús existentes...")
        for menu in current_menus:
            print(f"  - Eliminando: {menu.nombre} (ID: {menu.id})")
            db.delete(menu)
        
        db.commit()
        print("✓ Eliminación completada")
        
        # 3. Crear los nuevos menús de desarrollo
        print("\n✨ Creando menús de desarrollo...")
        for menu_data in MENUS_DEV:
            menu = MenuItem(**menu_data)
            db.add(menu)
            print(f"  + Creando: {menu_data['nombre']} (orden: {menu_data['orden']})")
        
        db.commit()
        print("✓ Creación completada")
        
        # 4. Verificar resultado
        final_menus = db.query(MenuItem).order_by(MenuItem.orden).all()
        print(f"\n✅ Total de menús en BD: {len(final_menus)}")
        print("\n📋 Menús finales:")
        for menu in final_menus:
            print(f"  {menu.id:3d} | {menu.nombre:25s} | {menu.href:30s} | orden: {menu.orden:3d}")
        
        print("\n🎉 Sincronización completada exitosamente!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la sincronización: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("="*80)
    print(" SINCRONIZACIÓN DE MENÚS RBAC: DESARROLLO → PRODUCCIÓN")
    print("="*80)
    sync_menus()
