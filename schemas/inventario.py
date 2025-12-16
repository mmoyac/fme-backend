"""
Schemas Pydantic para Inventario.
"""
from pydantic import BaseModel, Field
from typing import Optional


class InventarioBase(BaseModel):
    """Schema base de Inventario."""
    producto_id: int = Field(..., gt=0)
    local_id: int = Field(..., gt=0)
    cantidad_stock: int = Field(default=0)


class InventarioCreate(InventarioBase):
    """Schema para crear un Inventario."""
    pass


class InventarioUpdate(BaseModel):
    """Schema para actualizar un Inventario."""
    cantidad_stock: Optional[int] = Field(None)


class InventarioResponse(InventarioBase):
    """Schema de respuesta de Inventario."""
    id: int

    class Config:
        from_attributes = True
