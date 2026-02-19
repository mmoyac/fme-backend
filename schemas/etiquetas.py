"""
Schemas Pydantic para Etiquetas Nutricionales y Sellos de Advertencia.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ===========================
# Sellos de Advertencia
# ===========================

class SelloAdvertenciaBase(BaseModel):
    """Schema base de Sello de Advertencia."""
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = None
    color: str = Field(default="#000000", max_length=7)
    icono: Optional[str] = None
    orden: int = Field(default=0)
    activo: bool = Field(default=True)


class SelloAdvertenciaResponse(SelloAdvertenciaBase):
    """Schema de respuesta de Sello de Advertencia."""
    id: int

    class Config:
        from_attributes = True


# ===========================
# Información Nutricional
# ===========================

class InformacionNutricionalBase(BaseModel):
    """Schema base de Información Nutricional."""
    porcion_referencia: str = Field(default="100g", max_length=50)
    energia_kcal: Optional[Decimal] = Field(None, ge=0)
    proteinas_g: Optional[Decimal] = Field(None, ge=0)
    carbohidratos_g: Optional[Decimal] = Field(None, ge=0)
    azucares_g: Optional[Decimal] = Field(None, ge=0)
    grasas_totales_g: Optional[Decimal] = Field(None, ge=0)
    grasas_saturadas_g: Optional[Decimal] = Field(None, ge=0)
    grasas_trans_g: Optional[Decimal] = Field(None, ge=0)
    fibra_g: Optional[Decimal] = Field(None, ge=0)
    sodio_mg: Optional[Decimal] = Field(None, ge=0)
    colesterol_mg: Optional[Decimal] = Field(None, ge=0)
    calcio_mg: Optional[Decimal] = Field(None, ge=0)
    hierro_mg: Optional[Decimal] = Field(None, ge=0)
    vitamina_a_mcg: Optional[Decimal] = Field(None, ge=0)
    vitamina_c_mg: Optional[Decimal] = Field(None, ge=0)


class InformacionNutricionalCreate(InformacionNutricionalBase):
    """Schema para crear Información Nutricional."""
    producto_id: int


class InformacionNutricionalUpdate(BaseModel):
    """Schema para actualizar Información Nutricional."""
    porcion_referencia: Optional[str] = Field(None, max_length=50)
    energia_kcal: Optional[Decimal] = Field(None, ge=0)
    proteinas_g: Optional[Decimal] = Field(None, ge=0)
    carbohidratos_g: Optional[Decimal] = Field(None, ge=0)
    azucares_g: Optional[Decimal] = Field(None, ge=0)
    grasas_totales_g: Optional[Decimal] = Field(None, ge=0)
    grasas_saturadas_g: Optional[Decimal] = Field(None, ge=0)
    grasas_trans_g: Optional[Decimal] = Field(None, ge=0)
    fibra_g: Optional[Decimal] = Field(None, ge=0)
    sodio_mg: Optional[Decimal] = Field(None, ge=0)
    colesterol_mg: Optional[Decimal] = Field(None, ge=0)
    calcio_mg: Optional[Decimal] = Field(None, ge=0)
    hierro_mg: Optional[Decimal] = Field(None, ge=0)
    vitamina_a_mcg: Optional[Decimal] = Field(None, ge=0)
    vitamina_c_mg: Optional[Decimal] = Field(None, ge=0)


class InformacionNutricionalResponse(InformacionNutricionalBase):
    """Schema de respuesta de Información Nutricional."""
    id: int
    producto_id: int
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True


# ===========================
# Etiqueta Completa (combinada)
# ===========================

class EtiquetaProductoResponse(BaseModel):
    """Schema de respuesta con toda la información de etiqueta de un producto."""
    producto_id: int
    producto_nombre: str
    producto_sku: str
    codigo_barra: Optional[str] = None
    
    # Información nutricional (puede ser None si no está configurada)
    informacion_nutricional: Optional[InformacionNutricionalResponse] = None
    
    # Sellos de advertencia asociados
    sellos: List[SelloAdvertenciaResponse] = []

    class Config:
        from_attributes = True


# ===========================
# Asignación de Sellos
# ===========================

class AsignarSellosRequest(BaseModel):
    """Schema para asignar sellos a un producto."""
    sello_ids: List[int] = Field(..., description="Lista de IDs de sellos a asignar")
