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
    db: Session = Depends(get_db),
    tenant_id: int = None,
):
    """
    Obtener configuración de landing page para un tenant.

    Endpoint público (sin autenticación) que detecta el tenant automáticamente
    basándose en el dominio de la petición.

    Acepta ?tenant_id=X para superadmin que opera en un tenant específico.
    """
    from database.models import Tenant, ConfiguracionLanding, PaletaColores

    # Si viene tenant_id explícito (superadmin), usarlo directamente
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
    else:
        # Detectar tenant por dominio
        tenant = tenant_service.get_tenant_from_request(request, db)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    # Validar que el tenant esté activo
    tenant_service.validar_tenant_activo(tenant)
    
    # Buscar configuración de landing con JOIN a paleta_colores
    config = db.query(ConfiguracionLanding).filter(ConfiguracionLanding.tenant_id == tenant.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de landing no encontrada")
    
    # Determinar colores: usar paleta si existe, sino usar colores custom
    colores_final = {}
    if config.paleta_id:
        # Cargar colores de la paleta
        paleta = db.query(PaletaColores).filter(PaletaColores.id == config.paleta_id).first()
        if paleta:
            colores_final = {
                "primario": paleta.primario,
                "primario_light": paleta.primario_light,
                "primario_dark": paleta.primario_dark,
                "secundario": paleta.secundario,
                "secundario_light": paleta.secundario_light,
                "secundario_dark": paleta.secundario_dark,
                "acento": paleta.acento,
                "fondo_hero_inicio": paleta.fondo_hero_inicio,
                "fondo_hero_fin": paleta.fondo_hero_fin,
                "fondo_seccion": paleta.fondo_seccion
            }
        else:
            # Paleta no existe, usar colores custom
            colores_final = config.colores
    else:
        # Sin paleta, usar colores custom
        colores_final = config.colores
    
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
        "colores": colores_final,
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
        },
        "delivery": {
            "costo_fijo": float(config.costo_fijo_delivery) if config.costo_fijo_delivery is not None else None,
            "costo_por_km": float(config.costo_por_km_delivery) if config.costo_por_km_delivery is not None else None,
            "monto_minimo_gratis": float(config.monto_minimo_delivery_gratis) if config.monto_minimo_delivery_gratis is not None else None,
            "max_km": float(config.max_km_delivery) if config.max_km_delivery is not None else None
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