"""
Script para probar el hash de contraseña del tenant 3.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.database import SessionLocal
from database.models import User
from utils.security import verify_password

def main():
    db = SessionLocal()
    
    try:
        # Obtener usuario admin del tenant 3
        user = db.query(User).filter(
            User.email == 'admin@donajuanita.cl'
        ).first()
        
        if not user:
            print("❌ Usuario no encontrado")
            return
        
        print(f"✅ Usuario encontrado: {user.email}")
        print(f"   Tenant ID: {user.tenant_id}")
        print(f"   Hash almacenado: {user.hashed_password[:50]}...")
        
        # Probar contraseña correcta
        password_correcta = "admin123"
        resultado = verify_password(password_correcta, user.hashed_password)
        
        print(f"\n🔐 Verificación con '{password_correcta}': {'✅ VÁLIDA' if resultado else '❌ INVÁLIDA'}")
        
        # Probar contraseña incorrecta
        password_incorrecta = "wrong_password"
        resultado2 = verify_password(password_incorrecta, user.hashed_password)
        print(f"🔐 Verificación con '{password_incorrecta}': {'✅ VÁLIDA' if resultado2 else '❌ INVÁLIDA (correcto)'}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
