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
    # Información de tipo de venta (peso vs cantidad)
    tipo_venta_codigo: Optional[str] = None  # UNITARIO, PESO_SUELTO
    tipo_venta_nombre: Optional[str] = None

    class Config:
        from_attributes = True
