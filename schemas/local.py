"""
Schemas Pydantic para Local.
"""
from pydantic import BaseModel, Field
from typing import Optional


class LocalBase(BaseModel):
    """Schema base de Local."""
    nombre: str = Field(..., min_length=1, max_length=255)
    codigo: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = None
    activo: bool = True


class LocalCreate(LocalBase):
    """Schema para crear un Local."""
    pass


class LocalUpdate(BaseModel):
    """Schema para actualizar un Local."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    codigo: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = None
    activo: Optional[bool] = None


class LocalResponse(LocalBase):
    """Schema de respuesta de Local."""
    id: int

    class Config:
        from_attributes = True
