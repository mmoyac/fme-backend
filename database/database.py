"""
Configuración de la conexión a la base de datos con SQLAlchemy.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fme:fme@db:5432/fme_database")

# Crear el engine de SQLAlchemy
# Configuración optimizada para soportar cargas masivas
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Validar conexiones antes de usar
    pool_size=10,            # Aumentado de 5 (default) a 10
    max_overflow=20,         # Aumentado de 10 (default) a 20
    pool_recycle=3600        # Reciclar conexiones cada 1 hora (prevenir leaks)
)

# Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para los modelos
Base = declarative_base()

def get_db():
    """
    Generador de dependencia para obtener una sesión de base de datos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
