"""
Schemas Pydantic para tablas maestras del sistema de producción.
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


# ============================================
# CATEGORÍAS DE PRODUCTO
# ============================================

class CategoriaProductoBase(BaseModel):
    codigo: str = Field(..., description="Código único de la categoría")
    nombre: str = Field(..., description="Nombre de la categoría")
    descripcion: Optional[str] = None
    puntos_fidelidad: int = Field(default=0, description="Puntos que otorga por venta")
    activo: bool = True


class CategoriaProductoCreate(CategoriaProductoBase):
    pass


class CategoriaProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    puntos_fidelidad: Optional[int] = None
    activo: Optional[bool] = None


class CategoriaProducto(CategoriaProductoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE DOCUMENTO
# ============================================

class TipoDocumentoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de documento")
    nombre: str = Field(..., description="Nombre del tipo de documento")
    activo: bool = True


class TipoDocumentoCreate(TipoDocumentoBase):
    pass


class TipoDocumentoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = None


class TipoDocumento(TipoDocumentoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE PRODUCTO
# ============================================

class TipoProductoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo")
    nombre: str = Field(..., description="Nombre del tipo")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoProductoCreate(TipoProductoBase):
    pass


class TipoProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoProducto(TipoProductoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# UNIDADES DE MEDIDA
# ============================================

class UnidadMedidaBase(BaseModel):
    codigo: str = Field(..., description="Código único de la unidad")
    nombre: str = Field(..., description="Nombre completo")
    simbolo: str = Field(..., description="Símbolo (ej: kg, L, un)")
    tipo: Optional[str] = Field(None, description="CANTIDAD, PESO, VOLUMEN")
    factor_conversion: Optional[Decimal] = Field(None, description="Factor para convertir a unidad base")
    unidad_base_id: Optional[int] = Field(None, description="ID de la unidad base para conversiones")
    activo: bool = True


class UnidadMedidaCreate(UnidadMedidaBase):
    pass


class UnidadMedidaUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    tipo: Optional[str] = None
    factor_conversion: Optional[Decimal] = None
    unidad_base_id: Optional[int] = None
    activo: Optional[bool] = None


class UnidadMedida(UnidadMedidaBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# UNIDAD DE MEDIDA CON RELACIÓN
# ============================================

class UnidadMedidaConBase(UnidadMedida):
    """Unidad de medida con información de la unidad base."""
    unidad_base: Optional['UnidadMedida'] = None

    class Config:
        from_attributes = True
