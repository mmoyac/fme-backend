"""
Schemas Pydantic para LocalCliente (locales propios de un cliente).
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class LocalClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    direccion: str = Field(..., min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    activo: bool = True

class LocalClienteCreate(LocalClienteBase):
    pass

class LocalClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    direccion: Optional[str] = Field(None, min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    activo: Optional[bool] = None

class LocalClienteResponse(LocalClienteBase):
    id: int
    cliente_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
