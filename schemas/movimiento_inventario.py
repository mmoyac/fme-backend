"""
Schemas Pydantic para MovimientoInventario.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TransferenciaInventario(BaseModel):
    """Schema para transferir inventario entre locales."""
    producto_id: int = Field(..., gt=0)
    local_origen_id: int = Field(..., gt=0)
    local_destino_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    notas: Optional[str] = None


class AjusteInventario(BaseModel):
    """Schema para ajustar inventario (entrada/salida manual)."""
    producto_id: int = Field(..., gt=0)
    local_id: int = Field(..., gt=0)
    cantidad: int = Field(..., description="Positivo=entrada, Negativo=salida")
    notas: Optional[str] = None


class MovimientoInventarioResponse(BaseModel):
    """Schema de respuesta de MovimientoInventario."""
    id: int
    producto_id: int
    local_origen_id: Optional[int]
    local_destino_id: Optional[int]
    cantidad: int
    tipo_movimiento: str
    referencia_id: Optional[int]
    notas: Optional[str]
    usuario: str
    fecha_movimiento: datetime
    
    # Información adicional de relaciones
    producto: Optional[dict] = None
    local_origen: Optional[dict] = None
    local_destino: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
