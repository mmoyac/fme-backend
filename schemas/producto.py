"""
Schemas Pydantic para Producto.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ProductoBase(BaseModel):
    """Schema base de Producto."""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: str = Field(..., min_length=1, max_length=100)
    imagen_url: Optional[str] = None


class ProductoCreate(ProductoBase):
    """Schema para crear un Producto."""
    pass


class ProductoUpdate(BaseModel):
    """Schema para actualizar un Producto."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    imagen_url: Optional[str] = None


class ProductoResponse(ProductoBase):
    """Schema de respuesta de Producto."""
    id: int

    class Config:
        from_attributes = True
