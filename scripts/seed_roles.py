
import sys
import os
# Agregar root al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Role, User
from utils.security import get_password_hash
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://fme:fme@db:5432/fme_database"

def seed():
    print("Iniciando seed de roles y usuarios...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Definir roles
        roles_data = [
            {"nombre": "administrador", "descripcion": "Dueño del negocio - Acceso total operativo"},
            {"nombre": "tesorero", "descripcion": "Encargado de finanzas y pagos"},
            {"nombre": "vendedor", "descripcion": "Encargado de ventas y pedidos"},
        ]

        roles_map = {} # nombre -> id

        # Rol admin/superadmin ya existe presuntamente, lo obtenemos
        existing_admin = db.query(Role).filter(Role.nombre == "admin").first()
        if existing_admin:
            print(f"Rol existente: admin (ID: {existing_admin.id})")
            roles_map["admin"] = existing_admin.id
        
        for r_data in roles_data:
            role = db.query(Role).filter(Role.nombre == r_data["nombre"]).first()
            if not role:
                role = Role(nombre=r_data["nombre"], descripcion=r_data["descripcion"])
                db.add(role)
                db.commit()
                db.refresh(role)
                print(f"Rol creado: {role.nombre}")
            else:
                print(f"Rol ya existe: {role.nombre}")
            roles_map[role.nombre] = role.id

        # 2. Crear Usuarios Demo
        users_data = [
            {
                "email": "cliente@fme.cl",
                "password": "admin",
                "nombre": "Cliente Dueño",
                "role": "administrador"
            },
            {
                "email": "tesorero@fme.cl",
                "password": "admin",
                "nombre": "Juan Tesorero",
                "role": "tesorero"
            },
            {
                "email": "vendedor@fme.cl",
                "password": "admin",
                "nombre": "Ana Vendedora",
                "role": "vendedor"
            }
        ]

        for u_data in users_data:
            user = db.query(User).filter(User.email == u_data["email"]).first()
            if not user:
                hashed = get_password_hash(u_data["password"])
                user = User(
                    email=u_data["email"],
                    hashed_password=hashed,
                    nombre_completo=u_data["nombre"],
                    role_id=roles_map[u_data["role"]]
                )
                db.add(user)
                db.commit()
                print(f"Usuario creado: {u_data['email']} ({u_data['role']})")
            else:
                print(f"Usuario ya existe: {u_data['email']}")
                
    except Exception as e:
        print(f"Error durante seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
