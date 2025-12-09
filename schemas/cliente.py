"""
Schemas Pydantic para Cliente.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ClienteBase(BaseModel):
    """Schema base de Cliente."""
    nombre: str = Field(..., min_length=1, max_length=255)
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    comuna: Optional[str] = None


class ClienteCreate(ClienteBase):
    """Schema para crear un Cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para actualizar un Cliente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    comuna: Optional[str] = None


class ClienteResponse(ClienteBase):
    """Schema de respuesta de Cliente."""
    id: int

    class Config:
        from_attributes = True
