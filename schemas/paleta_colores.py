from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaletaColoresBase(BaseModel):
    nombre: str = Field(..., example="Turquesa Moderno")
    descripcion: Optional[str] = Field(None, example="Paleta corporativa azul-turquesa")
    primario: str = Field(..., example="#5EC8F2")
    primario_light: Optional[str] = Field(None, example="#AEEBFA")
    primario_dark: Optional[str] = Field(None, example="#2B7A9B")
    secundario: str = Field(..., example="#45A29A")
    secundario_light: Optional[str] = Field(None, example="#7FE3D6")
    secundario_dark: Optional[str] = Field(None, example="#2B5C54")
    acento: Optional[str] = Field(None, example="#FFD700")
    fondo_hero_inicio: Optional[str] = Field(None, example="#1E293B")
    fondo_hero_fin: Optional[str] = Field(None, example="#0F172A")
    fondo_seccion: Optional[str] = Field(None, example="#334155")
    es_publica: Optional[bool] = True

class PaletaColoresCreate(PaletaColoresBase):
    pass

class PaletaColoresUpdate(PaletaColoresBase):
    pass

class PaletaColoresResponse(PaletaColoresBase):
    id: int
    creado_por: Optional[int]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        orm_mode = True
