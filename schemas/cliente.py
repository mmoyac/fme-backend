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
    limite_credito: float = Field(default=0.0, ge=0, description="Límite de crédito del cliente")


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
    limite_credito: Optional[float] = Field(None, ge=0, description="Límite de crédito del cliente")


class ClienteResponse(ClienteBase):
    """Schema de respuesta de Cliente."""
    id: int
    credito_usado: float = Field(description="Crédito actualmente usado por el cliente")
    # Información de puntos
    puntos_disponibles: int = Field(default=0, description="Puntos disponibles del cliente")
    puntos_totales_ganados: int = Field(default=0, description="Total de puntos ganados histórico")
    puntos_totales_usados: int = Field(default=0, description="Total de puntos usados histórico")
    
    @property
    def credito_disponible(self) -> float:
        """Calcula el crédito disponible."""
        return float(self.limite_credito - self.credito_usado)
    
    @property
    def valor_puntos_disponibles(self) -> float:
        """Calcula el valor en pesos de los puntos disponibles (a $1 por punto)."""
        return float(self.puntos_disponibles * 1)

    class Config:
        from_attributes = True
