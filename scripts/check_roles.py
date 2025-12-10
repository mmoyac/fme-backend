
import sys
import os
# Agregar root al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Role
from dotenv import load_dotenv

load_dotenv()

# Usar URL interna de Docker si corre en contenedor
DATABASE_URL = "postgresql://fme:fme@db:5432/fme_database"

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    roles = db.query(Role).all()
    
    print(f"Roles encontrados: {len(roles)}")
    for role in roles:
        print(f"ID: {role.id}, Nombre: {role.nombre}")
        
    if not roles:
        print("No hay roles creados.")
        
except Exception as e:
    print(f"Error: {e}")
