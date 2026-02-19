"""
Script para crear el tenant "El Olivo" con su configuración de landing.
Ejecutar: docker-compose exec backend python scripts/seed_tenant_el_olivo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Tenant, ConfiguracionLanding


def seed_tenant_el_olivo():
    """Seed del tenant El Olivo."""
    db: Session = SessionLocal()
    
    try:
        # Verificar si ya existe
        existing = db.query(Tenant).filter(Tenant.codigo == 'el-olivo').first()
        if existing:
            print("✅ Tenant 'El Olivo' ya existe")
            return
        
        # Crear tenant
        tenant = Tenant(
            id=2,
            codigo='el-olivo',
            nombre='El Olivo',
            dominio_principal='elolivo.cl',
            subdomain='elolivo',
            activo=True
        )
        
        db.add(tenant)
        db.flush()  # Para obtener el ID
        
        print(f"✅ Tenant creado: {tenant.nombre} (ID: {tenant.id})")
        
        # Crear configuración de landing
        config = ConfiguracionLanding(
            tenant_id=tenant.id,
            
            # Branding
            logo_url='/logo-el-olivo.png',
            favicon_url='/favicon.ico',
            nombre_comercial='El Olivo',
            
            # Colores (mismos que Masas Estación)
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
            hero_titulo='Aceite de oliva premium directo del productor',
            hero_subtitulo='El mejor aceite de oliva extra virgen de Chile. 100% natural y prensado en frío.',
            hero_imagen_url='/hero-background.jpg',
            hero_cta_texto='Ver Productos',
            hero_cta_link='#productos',
            
            # Hero Badges
            hero_badges=[
                {"icono": "check-circle", "texto": "Extra virgen certificado"},
                {"icono": "check-circle", "texto": "Envío a todo Chile"},
                {"icono": "check-circle", "texto": "Productor directo"}
            ],
            
            # Beneficios
            beneficios=[
                {
                    "icono": "check-circle",
                    "titulo": "100% Natural",
                    "descripcion": "Aceite de oliva extra virgen sin aditivos ni conservantes"
                },
                {
                    "icono": "truck",
                    "titulo": "Envío a Domicilio",
                    "descripcion": "Llevamos nuestro aceite premium a tu hogar"
                },
                {
                    "icono": "currency-dollar",
                    "titulo": "Precio de Productor",
                    "descripcion": "Compra directo sin intermediarios y ahorra"
                },
                {
                    "icono": "cube",
                    "titulo": "Prensado en Frío",
                    "descripcion": "Método tradicional que preserva todas las propiedades"
                }
            ],
            
            # Footer / Contacto
            redes_sociales={
                "facebook": "https://www.facebook.com/elolivo/",
                "instagram": "https://www.instagram.com/elolivo/",
                "whatsapp": "+56987654321"
            },
            telefono='+56 9 8765 4321',
            email='contacto@elolivo.cl',
            direccion='Valle de Colchagua, Chile',
            
            # Otros textos
            texto_footer_descripcion='Aceite de oliva premium directo del productor a tu mesa.',
            texto_copyright='El Olivo. Todos los derechos reservados.',
            
            # SEO
            meta_title='El Olivo - Aceite de Oliva Extra Virgen Premium',
            meta_description='Compra aceite de oliva extra virgen premium directo del productor. 100% natural, prensado en frío y con envío a todo Chile.'
        )
        
        db.add(config)
        db.commit()
        
        print(f"✅ Configuración de landing creada para {tenant.nombre}")
        print(f"   - Dominio: {tenant.dominio_principal}")
        print(f"   - Subdomain: {tenant.subdomain}")
        print(f"   - Logo: {config.logo_url}")
        print(f"   - Hero: {config.hero_titulo}")
        print(f"\n🔗 Para probar, llama al endpoint:")
        print(f"   GET /api/config/landing?tenant_id={tenant.id}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Creando tenant 'El Olivo'...")
    seed_tenant_el_olivo()
    print("✅ Proceso completado")
