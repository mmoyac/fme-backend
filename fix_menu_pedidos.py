#!/usr/bin/env python3
"""
Script para verificar y arreglar el menú de pedidos en producción
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Role, MenuItem, User
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Usar la URL de la BD desde el environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fme:fme@localhost:5432/fme_database")
print(f"🔗 Conectando a: {DATABASE_URL}")

def fix_menu_pedidos():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("🔍 Verificando estado del menú...")
        
        # 1. Verificar si existe el item "Pedidos"
        pedidos_menu = db.query(MenuItem).filter(MenuItem.nombre == "Pedidos").first()
        
        if not pedidos_menu:
            print("❌ Menu 'Pedidos' NO existe. Creando...")
            pedidos_menu = MenuItem(
                nombre="Pedidos",
                href="/admin/pedidos", 
                icon="🛒",
                orden=2
            )
            db.add(pedidos_menu)
            db.commit()
            db.refresh(pedidos_menu)
            print("✅ Menu 'Pedidos' creado")
        else:
            print(f"✅ Menu 'Pedidos' existe: {pedidos_menu.href}")
        
        # 2. Verificar roles y sus permisos
        roles = db.query(Role).all()
        print(f"\n📋 Roles encontrados: {len(roles)}")
        
        for role in roles:
            print(f"\n🔑 Rol: {role.nombre}")
            print(f"   Menús asignados: {len(role.menus)}")
            
            # Listar menús actuales
            menu_names = [menu.nombre for menu in role.menus]
            print(f"   - {', '.join(menu_names) if menu_names else 'Ninguno'}")
            
            # Si es admin o vendedor, asegurar que tiene acceso a Pedidos
            if role.nombre.lower() in ['admin', 'administrador', 'vendedor']:
                if "Pedidos" not in menu_names:
                    print(f"   ⚠️ Faltan permisos de 'Pedidos', agregando...")
                    role.menus.append(pedidos_menu)
                    db.commit()
                    print(f"   ✅ Permisos de 'Pedidos' agregados a {role.nombre}")
        
        # 3. Verificar usuarios activos
        print(f"\n👥 Usuarios en el sistema:")
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            role_name = user.role.nombre if user.role else "Sin rol"
            menu_count = len(user.role.menus) if user.role else 0
            print(f"   - {user.email} ({role_name}) - {menu_count} menús")
            
        print(f"\n✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_menu_pedidos()