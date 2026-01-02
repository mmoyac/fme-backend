#!/usr/bin/env python3
"""
Script para actualizar el menú del Dashboard con estructura jerárquica.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models import MenuOption, Role
from sqlalchemy.orm import Session

def actualizar_menu_dashboard():
    """
    Actualiza el menú Dashboard para tener estructura jerárquica con:
    - Dashboard (principal)
    - Dashboard > Tablero de Ventas
    - Dashboard > Tablero de Cajas
    """
    db: Session = SessionLocal()
    
    try:
        # Verificar que existe el rol admin
        admin_role = db.query(Role).filter(Role.nombre == 'admin').first()
        if not admin_role:
            print("❌ Error: No existe el rol 'admin'. Ejecuta primero seed_menu_rbac.py")
            return False
        
        print("🔄 Actualizando menú Dashboard con estructura jerárquica...")
        
        # 1. Actualizar el menú Dashboard principal para que sea más descriptivo
        dashboard_menu = db.query(MenuOption).filter(MenuOption.href == '/admin/dashboard').first()
        if dashboard_menu:
            dashboard_menu.nombre = 'Dashboard'
            dashboard_menu.icon = '📊'
            print("✅ Actualizado menú Dashboard principal")
        else:
            # Crear el menú Dashboard si no existe
            dashboard_menu = MenuOption(
                nombre='Dashboard',
                href='/admin/dashboard',
                icon='📊',
                orden=1,
                role_id=admin_role.id
            )
            db.add(dashboard_menu)
            db.flush()  # Para obtener el ID
            print("✅ Creado menú Dashboard principal")
        
        # 2. Crear submenú para Tablero de Ventas (si no existe)
        ventas_menu = db.query(MenuOption).filter(MenuOption.href == '/admin/dashboard/ventas').first()
        if not ventas_menu:
            ventas_menu = MenuOption(
                nombre='Tablero de Ventas',
                href='/admin/dashboard/ventas',
                icon='📈',
                orden=11,  # Después del dashboard principal
                role_id=admin_role.id
            )
            db.add(ventas_menu)
            print("✅ Creado submenú: Tablero de Ventas")
        
        # 3. Crear submenú para Tablero de Cajas (si no existe)
        cajas_menu = db.query(MenuOption).filter(MenuOption.href == '/admin/dashboard/cajas').first()
        if not cajas_menu:
            cajas_menu = MenuOption(
                nombre='Tablero de Cajas',
                href='/admin/dashboard/cajas',
                icon='💰',
                orden=12,  # Después del tablero de ventas
                role_id=admin_role.id
            )
            db.add(cajas_menu)
            print("✅ Creado submenú: Tablero de Cajas")
        
        # 4. Eliminar el menú de "Caja" individual si existe (lo reemplazamos con Tablero de Cajas)
        caja_individual = db.query(MenuOption).filter(MenuOption.href == '/admin/caja').first()
        if caja_individual:
            db.delete(caja_individual)
            print("✅ Eliminado menú individual de Caja (ahora está en Dashboard)")
        
        # 5. Actualizar orden del menú principal de Caja para que sea una acción rápida
        # Buscar si existe un menú de caja en la raíz
        caja_principal = db.query(MenuOption).filter(MenuOption.nombre.ilike('%caja%')).filter(MenuOption.href == '/admin/caja').first()
        if caja_principal:
            # Lo mantenemos pero le cambiamos el nombre y orden
            caja_principal.nombre = 'Abrir Caja'
            caja_principal.icon = '🏪'
            caja_principal.orden = 25  # Después de los tableros
            print("✅ Actualizado menú 'Abrir Caja' como acción rápida")
        
        db.commit()
        
        print("\n🎉 Menú Dashboard actualizado exitosamente!")
        print("📋 Estructura actual del menú:")
        print("   📊 Dashboard (página principal con resumen)")
        print("   ├── 📈 Tablero de Ventas (/admin/dashboard/ventas)")
        print("   └── 💰 Tablero de Cajas (/admin/dashboard/cajas)")
        print("   🏪 Abrir Caja (acción rápida)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando menú: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = actualizar_menu_dashboard()
    if success:
        print("\n✅ Script ejecutado exitosamente")
    else:
        print("\n❌ Script falló")
        sys.exit(1)