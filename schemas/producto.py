"""
Schemas Pydantic para Producto.
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class ProductoBase(BaseModel):
    """Schema base de Producto."""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: str = Field(..., min_length=1, max_length=100)
    imagen_url: Optional[str] = None
    categoria_id: int
    tipo_producto_id: int
    unidad_medida_id: int
    precio_compra: Optional[Decimal] = None
    costo_fabricacion: Optional[Decimal] = None
    es_vendible: bool = True
    es_vendible_web: bool = False
    es_ingrediente: bool = False
    tiene_receta: bool = False
    activo: bool = True


class ProductoCreate(ProductoBase):
    """Schema para crear un Producto."""
    pass


class ProductoUpdate(BaseModel):
    """Schema para actualizar un Producto."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    imagen_url: Optional[str] = None
    categoria_id: Optional[int] = None
    tipo_producto_id: Optional[int] = None
    unidad_medida_id: Optional[int] = None
    precio_compra: Optional[Decimal] = None
    costo_fabricacion: Optional[Decimal] = None
    es_vendible: Optional[bool] = None
    es_vendible_web: Optional[bool] = None
    es_ingrediente: Optional[bool] = None
    tiene_receta: Optional[bool] = None
    activo: Optional[bool] = None


class ProductoResponse(ProductoBase):
    """Schema de respuesta de Producto."""
    id: int

    class Config:
        from_attributes = True
