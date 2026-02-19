"""
Schemas Pydantic para ConfiguracionLanding (White-label).
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List, Any
from datetime import datetime


class ColorSchema(BaseModel):
    """Schema para colores del tenant."""
    primario: str = Field(..., description="Color primario en formato hex (#RRGGBB)")
    secundario: str = Field(..., description="Color secundario en formato hex")
    acento: Optional[str] = Field(None, description="Color de acento en formato hex")
    primario_light: Optional[str] = None
    primario_dark: Optional[str] = None
    secundario_light: Optional[str] = None
    secundario_dark: Optional[str] = None
    fondo_hero_inicio: Optional[str] = None
    fondo_hero_fin: Optional[str] = None
    fondo_seccion: Optional[str] = None


class BadgeSchema(BaseModel):
    """Schema para badges del hero."""
    icono: str = Field(..., description="Emoji o nombre de icono")
    texto: str = Field(..., description="Texto del badge")


class BeneficioSchema(BaseModel):
    """Schema para beneficios."""
    icono: str = Field(..., description="Emoji o nombre de icono")
    titulo: str = Field(..., description="Título del beneficio")
    descripcion: str = Field(..., description="Descripción del beneficio")


class RedesSocialesSchema(BaseModel):
    """Schema para redes sociales."""
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    whatsapp: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None


class ConfiguracionLandingBase(BaseModel):
    """Schema base de ConfiguracionLanding."""
    # Branding
    logo_url: Optional[str] = Field(None, max_length=255)
    favicon_url: Optional[str] = Field(None, max_length=255)
    nombre_comercial: Optional[str] = Field(None, max_length=100)
    
    # Colores
    colores: Dict[str, Any] = Field(default_factory=dict)
    
    # Hero Section
    hero_titulo: Optional[str] = None
    hero_subtitulo: Optional[str] = None
    hero_imagen_url: Optional[str] = Field(None, max_length=255)
    hero_cta_texto: Optional[str] = Field(None, max_length=50)
    hero_cta_link: Optional[str] = Field(None, max_length=100)
    hero_badges: List[Dict[str, str]] = Field(default_factory=list)
    
    # Beneficios
    beneficios: List[Dict[str, str]] = Field(default_factory=list)
    
    # Footer / Contacto
    redes_sociales: Dict[str, str] = Field(default_factory=dict)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = None
    texto_footer_descripcion: Optional[str] = None
    texto_copyright: Optional[str] = Field(None, max_length=200)
    
    # SEO Metadata
    meta_title: Optional[str] = Field(None, max_length=100)
    meta_description: Optional[str] = None
    
    # Opciones de Visualización (Modo Catálogo)
    mostrar_precios: bool = Field(default=True, description="Si se muestran los precios en la landing")
    mostrar_stock: bool = Field(default=True, description="Si se muestra el stock disponible")
    habilitar_carrito: bool = Field(default=True, description="Si se habilita el carrito de compras")


class ConfiguracionLandingCreate(ConfiguracionLandingBase):
    """Schema para crear ConfiguracionLanding."""
    tenant_id: int = Field(..., gt=0)


class ConfiguracionLandingUpdate(BaseModel):
    """Schema para actualizar ConfiguracionLanding (todos los campos opcionales)."""
    # Branding
    logo_url: Optional[str] = Field(None, max_length=255)
    favicon_url: Optional[str] = Field(None, max_length=255)
    nombre_comercial: Optional[str] = Field(None, max_length=100)
    
    # Colores
    colores: Optional[Dict[str, Any]] = None
    
    # Hero Section
    hero_titulo: Optional[str] = None
    hero_subtitulo: Optional[str] = None
    hero_imagen_url: Optional[str] = Field(None, max_length=255)
    hero_cta_texto: Optional[str] = Field(None, max_length=50)
    hero_cta_link: Optional[str] = Field(None, max_length=100)
    hero_badges: Optional[List[Dict[str, str]]] = None
    
    # Beneficios
    beneficios: Optional[List[Dict[str, str]]] = None
    
    # Footer / Contacto
    redes_sociales: Optional[Dict[str, str]] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = None
    texto_footer_descripcion: Optional[str] = None
    texto_copyright: Optional[str] = Field(None, max_length=200)
    
    # SEO Metadata
    meta_title: Optional[str] = Field(None, max_length=100)
    meta_description: Optional[str] = None
    
    # Opciones de Visualización (Modo Catálogo)
    mostrar_precios: Optional[bool] = None
    mostrar_stock: Optional[bool] = None
    habilitar_carrito: Optional[bool] = None


class ConfiguracionLandingResponse(ConfiguracionLandingBase):
    """Schema de respuesta de ConfiguracionLanding."""
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
