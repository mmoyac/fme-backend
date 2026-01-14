"""
Schemas Pydantic para TipoPedido.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class LocalBasico(BaseModel):
    """Schema básico de Local."""
    id: int
    codigo: str
    nombre: str
    
    model_config = ConfigDict(from_attributes=True)


class TipoPedidoBase(BaseModel):
    """Schema base de TipoPedido."""
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    local_despacho_default_id: Optional[int] = Field(None, description="ID del local de despacho por defecto")
    activo: bool = Field(default=True)


class TipoPedidoCreate(TipoPedidoBase):
    """Schema para crear un TipoPedido."""
    pass


class TipoPedidoUpdate(BaseModel):
    """Schema para actualizar un TipoPedido."""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    local_despacho_default_id: Optional[int] = Field(None, description="ID del local de despacho por defecto")
    activo: Optional[bool] = None


class TipoPedidoResponse(TipoPedidoBase):
    """Schema de respuesta de TipoPedido."""
    id: int
    local_despacho_default: Optional[LocalBasico] = Field(None, description="Información del local por defecto")
    
    model_config = ConfigDict(from_attributes=True)