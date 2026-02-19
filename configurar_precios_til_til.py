"""
Script para copiar precios del local WEB al local Til Til
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar a la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://fme:fme@localhost:5432/fme_database')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def configurar_precios_til_til():
    session = Session()
    
    try:
        # 1. Buscar local WEB y Til Til
        result_web = session.execute(
            text("SELECT id FROM locales WHERE codigo = 'WEB' LIMIT 1")
        ).fetchone()
        
        result_til_til = session.execute(
            text("SELECT id, nombre FROM locales WHERE LOWER(nombre) LIKE '%til til%' LIMIT 1")
        ).fetchone()
        
        if not result_web:
            print("❌ No se encontró el local WEB")
            return
            
        if not result_til_til:
            print("❌ No se encontró el local Til Til")
            print("\n📋 Locales disponibles:")
            locales = session.execute(text("SELECT id, nombre, codigo FROM locales")).fetchall()
            for local in locales:
                print(f"  - ID: {local[0]}, Nombre: {local[1]}, Código: {local[2]}")
            return
        
        local_web_id = result_web[0]
        local_til_til_id = result_til_til[0]
        local_til_til_nombre = result_til_til[1]
        
        print(f"✅ Local WEB encontrado (ID: {local_web_id})")
        print(f"✅ Local {local_til_til_nombre} encontrado (ID: {local_til_til_id})")
        
        # 2. Verificar precios existentes en Til Til
        precios_existentes = session.execute(
            text("SELECT COUNT(*) FROM precios WHERE local_id = :local_id"),
            {"local_id": local_til_til_id}
        ).scalar()
        
        print(f"\n📊 Precios actuales en {local_til_til_nombre}: {precios_existentes}")
        
        # 3. Obtener precios del local WEB
        precios_web = session.execute(
            text("""
                SELECT producto_id, monto_precio 
                FROM precios 
                WHERE local_id = :local_id
            """),
            {"local_id": local_web_id}
        ).fetchall()
        
        print(f"📊 Precios en local WEB: {len(precios_web)}")
        
        if len(precios_web) == 0:
            print("❌ No hay precios en el local WEB para copiar")
            return
        
        # 4. Copiar precios
        print(f"\n🔄 Copiando precios del local WEB a {local_til_til_nombre}...")
        
        copied = 0
        updated = 0
        
        for producto_id, monto_precio in precios_web:
            # Verificar si ya existe
            existing = session.execute(
                text("""
                    SELECT id FROM precios 
                    WHERE producto_id = :producto_id AND local_id = :local_id
                """),
                {"producto_id": producto_id, "local_id": local_til_til_id}
            ).fetchone()
            
            if existing:
                # Actualizar
                session.execute(
                    text("""
                        UPDATE precios 
                        SET monto_precio = :monto_precio
                        WHERE producto_id = :producto_id AND local_id = :local_id
                    """),
                    {
                        "monto_precio": monto_precio,
                        "producto_id": producto_id,
                        "local_id": local_til_til_id
                    }
                )
                updated += 1
            else:
                # Insertar
                session.execute(
                    text("""
                        INSERT INTO precios (producto_id, local_id, monto_precio)
                        VALUES (:producto_id, :local_id, :monto_precio)
                    """),
                    {
                        "producto_id": producto_id,
                        "local_id": local_til_til_id,
                        "monto_precio": monto_precio
                    }
                )
                copied += 1
        
        session.commit()
        
        print(f"\n✅ Proceso completado:")
        print(f"  - Precios nuevos copiados: {copied}")
        print(f"  - Precios actualizados: {updated}")
        print(f"  - Total: {copied + updated}")
        
        # 5. Verificar resultado final
        total_final = session.execute(
            text("SELECT COUNT(*) FROM precios WHERE local_id = :local_id"),
            {"local_id": local_til_til_id}
        ).scalar()
        
        print(f"\n📊 Precios finales en {local_til_til_nombre}: {total_final}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    print("🔧 Configurando precios para local Til Til...")
    print("=" * 60)
    configurar_precios_til_til()
    print("=" * 60)
