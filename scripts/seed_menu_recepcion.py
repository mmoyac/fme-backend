"""
Script para agregar el menú de Recepción de Mercancías al sistema RBAC
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from database.database import engine
from database.models import MenuItem, Role


def add_menu_recepcion():
    """Agregar menú de Recepción de Mercancías."""
    with Session(engine) as db:
        print("🚛 Agregando menú de Recepción de Mercancías...")
        
        # 1. Crear/Buscar Menu Item
        menu_recepcion = db.query(MenuItem).filter(MenuItem.href == "/admin/recepcion").first()
        if not menu_recepcion:
            menu_recepcion = MenuItem(
                nombre="Recepción de Mercancías",
                href="/admin/recepcion", 
                icon="🚛",
                orden=15  # Después de Compras
            )
            db.add(menu_recepcion)
            db.commit()
            db.refresh(menu_recepcion)
            print(f"  ✅ Menú creado: {menu_recepcion.nombre}")
        else:
            print(f"  ⏭️  Menú ya existe: {menu_recepcion.nombre}")
        
        # 2. Asignar a roles con permisos
        roles_con_acceso = ["admin", "bodeguero", "supervisor"]
        
        for nombre_rol in roles_con_acceso:
            rol = db.query(Role).filter(Role.nombre == nombre_rol).first()
            if rol:
                # Verificar si ya tiene el menú asignado
                if menu_recepcion not in rol.menus:
                    rol.menus.append(menu_recepcion)
                    print(f"  ✅ Menú asignado al rol: {nombre_rol}")
                else:
                    print(f"  ⏭️  Rol {nombre_rol} ya tiene acceso")
            else:
                print(f"  ⚠️  Rol {nombre_rol} no encontrado")
        
        # 3. Commit final
        db.commit()
        
        print("\n✅ Menú de Recepción de Mercancías configurado exitosamente!")
        print("\n👥 Roles con acceso:")
        for nombre_rol in roles_con_acceso:
            rol = db.query(Role).filter(Role.nombre == nombre_rol).first()
            if rol and menu_recepcion in rol.menus:
                print(f"   • {rol.nombre}")
        
        print("\n📋 Información del menú:")
        print(f"   • Nombre: {menu_recepcion.nombre}")
        print(f"   • Ruta: {menu_recepcion.href}")
        print(f"   • Icono: {menu_recepcion.icon}")
        print(f"   • Orden: {menu_recepcion.orden}")


if __name__ == "__main__":
    add_menu_recepcion()