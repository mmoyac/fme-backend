"""
Script temporal para re-crear usuarios del tenant 3 con hash correcto.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.database import SessionLocal
from database.models import User
from utils.security import get_password_hash

def main():
    db = SessionLocal()
    
    try:
        # Obtener locales del tenant 3
        locales = {
            'MAIPU': 10,  # ID del local MAIPU
            'PUDAHUEL': 11  # ID del local PUDAHUEL
        }
        
        usuarios = [
            {
                'email': 'admin@donajuanita.cl',
                'nombre_completo': 'Juanita Pérez',
                'password': 'admin123',
                'role_id': 1,
                'local_defecto_id': locales['MAIPU']
            },
            {
                'email': 'vendedor.maipu@donajuanita.cl',
                'nombre_completo': 'Pedro González',
                'password': 'vendedor123',
                'role_id': 2,
                'local_defecto_id': locales['MAIPU']
            },
            {
                'email': 'vendedor.pudahuel@donajuanita.cl',
                'nombre_completo': 'María Silva',
                'password': 'vendedor123',
                'role_id': 2,
                'local_defecto_id': locales['PUDAHUEL']
            }
        ]
        
        for user_data in usuarios:
            user = User(
                tenant_id=3,
                email=user_data['email'],
                nombre_completo=user_data['nombre_completo'],
                hashed_password=get_password_hash(user_data['password']),
                role_id=user_data['role_id'],
                local_defecto_id=user_data['local_defecto_id'],
                is_active=True
            )
            db.add(user)
            print(f"✅ Usuario creado: {user_data['email']}")
        
        db.commit()
        print("\n✅ Usuarios del tenant 3 re-creados exitosamente")
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
