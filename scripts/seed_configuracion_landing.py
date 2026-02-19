"""
Script para cargar la configuración inicial de la landing page de Masas Estación.
Ejecutar: docker-compose exec backend python scripts/seed_configuracion_landing.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Tenant, ConfiguracionLanding


def seed_configuracion_landing():
    """Seed de configuración landing para Masas Estación."""
    db: Session = SessionLocal()
    
    try:
        # Verificar si ya existe configuración
        existing = db.query(ConfiguracionLanding).filter(ConfiguracionLanding.tenant_id == 1).first()
        if existing:
            print("✅ Configuración de landing ya existe para Masas Estación")
            return
        
        # Verificar que existe el tenant
        tenant = db.query(Tenant).filter(Tenant.id == 1).first()
        if not tenant:
            print("❌ Error: No existe el tenant con id=1")
            return
        
        # Crear configuración de landing
        config = ConfiguracionLanding(
            tenant_id=1,
            
            # Branding
            logo_url='/logo.png',
            favicon_url='/favicon.ico',
            nombre_comercial='Masas Estación',
            
            # Colores
            colores={
                "primario": "#5EC8F2",
                "primario_light": "#90DCFF",
                "primario_dark": "#45A29A",
                "secundario": "#45A29A",
                "secundario_light": "#63C0B8",
                "secundario_dark": "#31847C",
                "fondo_hero_inicio": "#0F172A",
                "fondo_hero_fin": "#1E293B",
                "fondo_seccion": "#1E293B"
            },
            
            # Hero Section
            hero_titulo='Las mejores masas frescas a tu mesa',
            hero_subtitulo='Masas de Empanadas y Sopaipillas frescas. Directo de fábrica.',
            hero_imagen_url='/hero-background.jpg',
            hero_cta_texto='Ver Catálogo Completo',
            hero_cta_link='#productos',
            
            # Hero Badges
            hero_badges=[
                {"icono": "check-circle", "texto": "Calidad garantizada"},
                {"icono": "check-circle", "texto": "Envío a domicilio"},
                {"icono": "check-circle", "texto": "Precios de fábrica"}
            ],
            
            # Beneficios
            beneficios=[
                {
                    "icono": "check-circle",
                    "titulo": "Calidad Artesanal",
                    "descripcion": "Elaboradas con ingredientes premium y recetas tradicionales"
                },
                {
                    "icono": "truck",
                    "titulo": "Envíos a Domicilio",
                    "descripcion": "Llevamos nuestros productos frescos directamente a tu hogar"
                },
                {
                    "icono": "currency-dollar",
                    "titulo": "Precios de Fábrica",
                    "descripcion": "Compra directo del productor y ahorra en cada pedido"
                },
                {
                    "icono": "cube",
                    "titulo": "Masas Congeladas",
                    "descripcion": "Listas para usar cuando las necesites, sin perder frescura"
                }
            ],
            
            # Footer / Contacto
            redes_sociales={
                "facebook": "https://www.facebook.com/masas.estacion/",
                "instagram": "https://www.instagram.com/fabrica_masas_estacion_spa/",
                "whatsapp": "+56912345678"
            },
            telefono='+56 9 1234 5678',
            email='contacto@masasestacion.cl',
            direccion='Santiago, Chile',
            
            # Otros textos
            texto_footer_descripcion='Las mejores masas frescas directo de fábrica a tu mesa.',
            texto_copyright='Masas Estación. Todos los derechos reservados.',
            
            # SEO
            meta_title='Masas Estación - Masas Frescas de Fábrica',
            meta_description='Compra masas de empanadas y sopaipillas frescas directo de fábrica. Calidad artesanal, envío a domicilio y precios competitivos.'
        )
        
        db.add(config)
        db.commit()
        
        print("✅ Configuración de landing creada exitosamente para Masas Estación")
        print(f"   - Tenant: {tenant.nombre}")
        print(f"   - Dominio: {tenant.dominio_principal}")
        print(f"   - Logo: {config.logo_url}")
        print(f"   - Hero Título: {config.hero_titulo}")
        print(f"   - Beneficios: {len(config.beneficios)} items")
        
    except Exception as e:
        print(f"❌ Error al crear configuración: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Iniciando seed de configuración landing...")
    seed_configuracion_landing()
    print("✅ Proceso completado")
