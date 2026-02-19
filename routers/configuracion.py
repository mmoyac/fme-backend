"""
Router para configuraciones y datos básicos del sistema (sin autenticación).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database.database import get_db
from services import tenant_service

router = APIRouter()


# ========================================
# CONFIGURACIÓN MULTI-TENANT (LANDING)
# ========================================

@router.get("/landing")
async def get_landing_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Obtener configuración de landing page para un tenant.
    
    Endpoint público (sin autenticación) que detecta el tenant automáticamente
    basándose en el dominio de la petición.
    
    Ejemplos:
    - masasestacion.cl → Tenant 1
    - elolivo.masasestacion.cl → Tenant 2
    - localhost → Tenant 1 (desarrollo)
    """
    from database.models import Tenant, ConfiguracionLanding
    
    # Detectar tenant por dominio
    tenant = tenant_service.get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    # Validar que el tenant esté activo
    tenant_service.validar_tenant_activo(tenant)
    
    # Buscar configuración de landing
    config = db.query(ConfiguracionLanding).filter(ConfiguracionLanding.tenant_id == tenant.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de landing no encontrada")
    
    # Retornar configuración completa
    return {
        "tenant": {
            "id": tenant.id,
            "codigo": tenant.codigo,
            "nombre": tenant.nombre,
            "dominio_principal": tenant.dominio_principal
        },
        "branding": {
            "logo_url": config.logo_url,
            "favicon_url": config.favicon_url,
            "nombre_comercial": config.nombre_comercial
        },
        "colores": config.colores,
        "hero": {
            "titulo": config.hero_titulo,
            "subtitulo": config.hero_subtitulo,
            "imagen_url": config.hero_imagen_url,
            "cta_texto": config.hero_cta_texto,
            "cta_link": config.hero_cta_link,
            "badges": config.hero_badges
        },
        "beneficios": config.beneficios,
        "footer": {
            "redes_sociales": config.redes_sociales,
            "telefono": config.telefono,
            "email": config.email,
            "direccion": config.direccion,
            "descripcion": config.texto_footer_descripcion,
            "copyright": config.texto_copyright
        },
        "seo": {
            "title": config.meta_title,
            "description": config.meta_description
        },
        "displaySettings": {
            "mostrar_precios": config.mostrar_precios,
            "mostrar_stock": config.mostrar_stock,
            "habilitar_carrito": config.habilitar_carrito
        }
    }


@router.get("/tenant/{codigo}")
async def get_tenant_by_code(
    codigo: str,
    db: Session = Depends(get_db)
):
    """
    Obtener información básica de un tenant por su código.
    Útil para validar existencia antes de cargar configuración completa.
    """
    from database.models import Tenant
    
    tenant = db.query(Tenant).filter(
        Tenant.codigo == codigo
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    # Validar que el tenant esté activo
    tenant_service.validar_tenant_activo(tenant)
    
    return {
        "id": tenant.id,
        "codigo": tenant.codigo,
        "nombre": tenant.nombre,
        "dominio_principal": tenant.dominio_principal,
        "subdomain": tenant.subdomain
    }


# ========================================
# CONFIGURACIONES GENERALES
# ========================================


@router.get("/tipos-documento")
def listar_tipos_documento(
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Listar tipos de documento tributario disponibles.
    Endpoint público necesario para el frontend.
    """
    from database.models import TipoDocumento
    
    query = db.query(TipoDocumento)
    
    if activo is not None:
        query = query.filter(TipoDocumento.activo == activo)
    
    tipos = query.order_by(TipoDocumento.nombre).all()
    
    return [
        {
            "id": tipo.id,
            "codigo": tipo.codigo,
            "nombre": tipo.nombre,
            "descripcion": tipo.descripcion,
            "activo": tipo.activo
        }
        for tipo in tipos
    ]


@router.get("/medios-pago")
def listar_medios_pago(
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Listar medios de pago disponibles.
    Endpoint público necesario para el frontend.
    """
    from database.models import MedioPago
    
    query = db.query(MedioPago)
    
    if activo is not None:
        query = query.filter(MedioPago.activo == activo)
    
    medios = query.order_by(MedioPago.nombre).all()
    
    return [
        {
            "id": medio.id,
            "codigo": medio.codigo,
            "nombre": medio.nombre,
            "descripcion": medio.descripcion,
            "permite_cheque": medio.permite_cheque,
            "activo": medio.activo
        }
        for medio in medios
    ]