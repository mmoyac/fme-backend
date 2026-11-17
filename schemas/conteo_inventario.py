"""
Schemas Pydantic para Conteo de Inventario (change OpenSpec: add-conteo-inventario).
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ConteoCreate(BaseModel):
    local_id: int = Field(..., gt=0)
    tipo: Literal["COMPLETO", "PARCIAL"]
    observacion: Optional[str] = None


class ConteoAgregarItems(BaseModel):
    """Agregar productos a un conteo: por lista de ids y/o por categoría."""
    producto_ids: List[int] = Field(default_factory=list)
    categoria_id: Optional[int] = None


class ConteoItemUpdate(BaseModel):
    # La validación >= 0 se hace en el servicio para responder 400 (spec), no 422.
    cantidad_contada: float


class ConteoItemResponse(BaseModel):
    id: int
    producto_id: int
    sku: Optional[str] = None
    producto_nombre: Optional[str] = None
    categoria_id: Optional[int] = None
    categoria_nombre: Optional[str] = None
    unidad: Optional[str] = None
    stock_sistema: Optional[float] = None
    stock_actual: Optional[float] = None
    cantidad_contada: Optional[float] = None
    diferencia: Optional[float] = None
    ajuste_aplicado: Optional[float] = None
    usuario_captura_id: Optional[int] = None
    usuario_captura: Optional[str] = None
    fecha_captura: Optional[datetime] = None


class ConteoResumen(BaseModel):
    id: int
    local_id: int
    local_nombre: Optional[str] = None
    tipo: str
    estado: str
    observacion: Optional[str] = None
    usuario_creador_id: int
    usuario_creador: Optional[str] = None
    fecha_inicio: datetime
    usuario_cierre_id: Optional[int] = None
    usuario_cierre: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    total_items: int = 0
    items_contados: int = 0
    items_con_diferencia: int = 0


class ConteoDetalle(ConteoResumen):
    items: List[ConteoItemResponse] = Field(default_factory=list)
