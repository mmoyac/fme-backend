#!/bin/bash
set -e

echo "🔄 Esperando a que PostgreSQL esté listo..."
python << 'END'
import time
import sys
from sqlalchemy import create_engine, text
import os

max_retries = 30
retry_count = 0
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    print("❌ DATABASE_URL no está configurada")
    sys.exit(1)

while retry_count < max_retries:
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL está listo")
        break
    except Exception as e:
        retry_count += 1
        print(f"⏳ PostgreSQL no está listo - esperando... (intento {retry_count}/{max_retries})")
        time.sleep(2)

if retry_count == max_retries:
    print("❌ No se pudo conectar a PostgreSQL después de 30 intentos")
    sys.exit(1)
END

echo "🔄 Ejecutando migraciones de Alembic..."
alembic upgrade head

echo "✅ Migraciones aplicadas exitosamente"

echo "🚀 Iniciando servidor FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
