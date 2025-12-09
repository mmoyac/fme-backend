"""
Schemas Pydantic para Precio.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PrecioBase(BaseModel):
    """Schema base de Precio."""
    producto_id: int = Field(..., gt=0)
    local_id: int = Field(..., gt=0)
    monto_precio: float = Field(..., gt=0)


class PrecioCreate(PrecioBase):
    """Schema para crear un Precio."""
    pass


class PrecioUpdate(BaseModel):
    """Schema para actualizar un Precio."""
    monto_precio: Optional[float] = Field(None, gt=0)


class PrecioResponse(PrecioBase):
    """Schema de respuesta de Precio."""
    id: int
    fecha_vigencia: datetime

    class Config:
        from_attributes = True
