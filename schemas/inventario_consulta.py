"""
Schemas Pydantic para Inventario y consultas de disponibilidad.
"""
from pydantic import BaseModel
from typing import List


# Schemas para resumen de inventario
class InventarioResumen(BaseModel):
    """Schema para resumen de inventario por producto."""
    sku: str
    nombre: str
    stock_total: int

    class Config:
        from_attributes = True


# Schemas para detalle de inventario por local
class InventarioLocalDetalle(BaseModel):
    """Schema para detalle de stock en un local específico."""
    local: str
    direccion: str
    stock: int

    class Config:
        from_attributes = True


class InventarioDetalle(BaseModel):
    """Schema para detalle completo de inventario de un producto."""
    sku: str
    nombre: str
    descripcion: str | None
    stock_total: int
    detalle_locales: List[InventarioLocalDetalle]

    class Config:
        from_attributes = True
