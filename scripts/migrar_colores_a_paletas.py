# Script para poblar la tabla paleta_colores a partir de configuracion_landing
from database.database import SessionLocal
from database.models import ConfiguracionLanding, PaletaColores
from sqlalchemy.orm import Session

def migrar_colores_a_paletas():
    db: Session = SessionLocal()
    try:
        configs = db.query(ConfiguracionLanding).all()
        for config in configs:
            colores = config.colores or {}
            nombre = f"Paleta {config.tenant_id}"
            paleta = PaletaColores(
                nombre=nombre,
                descripcion=f"Migrada desde tenant {config.tenant_id}",
                primario=colores.get("primario"),
                primario_light=colores.get("primario_light"),
                primario_dark=colores.get("primario_dark"),
                secundario=colores.get("secundario"),
                secundario_light=colores.get("secundario_light"),
                secundario_dark=colores.get("secundario_dark"),
                acento=colores.get("acento"),
                fondo_hero_inicio=colores.get("fondo_hero_inicio"),
                fondo_hero_fin=colores.get("fondo_hero_fin"),
                fondo_seccion=colores.get("fondo_seccion"),
                es_publica=True
            )
            db.add(paleta)
        db.commit()
        print(f"✅ Paletas migradas: {len(configs)}")
    finally:
        db.close()

if __name__ == "__main__":
    migrar_colores_a_paletas()
