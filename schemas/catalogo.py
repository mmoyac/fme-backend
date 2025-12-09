"""
Schemas Pydantic para catálogo de productos.
"""
from pydantic import BaseModel
from typing import Optional


class ProductoCatalogo(BaseModel):
    """Schema para producto en catálogo web."""
    sku: str
    nombre: str
    descripcion: Optional[str]
    imagen_url: Optional[str]
    precio: float
    stock_total: int

    class Config:
        from_attributes = True
