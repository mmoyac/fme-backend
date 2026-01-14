"""
Schemas Pydantic para TipoDocumento.
"""
from pydantic import BaseModel, Field
from typing import Optional


class TipoDocumentoBase(BaseModel):
    """Schema base de TipoDocumento."""
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    activo: bool = Field(default=True)


class TipoDocumentoCreate(TipoDocumentoBase):
    """Schema para crear un TipoDocumento."""
    pass


class TipoDocumentoUpdate(BaseModel):
    """Schema para actualizar un TipoDocumento."""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoDocumentoResponse(TipoDocumentoBase):
    """Schema de respuesta de TipoDocumento."""
    id: int
    
    class Config:
        from_attributes = True