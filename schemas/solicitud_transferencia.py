"""
Schemas Pydantic para SolicitudTransferencia e ItemSolicitudTransferencia.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ItemSolicitudTransferenciaCreate(BaseModel):
    producto_id: int
    cantidad_solicitada: int
    cantidad_aprobada: Optional[int] = None

class ItemSolicitudTransferenciaResponse(ItemSolicitudTransferenciaCreate):
    solicitud_item_id: int
    movimiento_inventario_id: Optional[int] = None

class SolicitudTransferenciaCreate(BaseModel):
    tenant_id: int
    local_origen_id: int
    local_destino_id: int
    usuario_solicitante_id: int
    estado_id: int
    nota: Optional[str] = None
    items: List[ItemSolicitudTransferenciaCreate]

class SolicitudTransferenciaUpdate(BaseModel):
    estado_id: Optional[int] = None
    nota: Optional[str] = None
    items: Optional[List[ItemSolicitudTransferenciaCreate]] = None

class SolicitudTransferenciaResponse(BaseModel):
    solicitud_id: int
    tenant_id: int
    local_origen_id: int
    local_destino_id: int
    usuario_solicitante_id: int
    estado_id: int
    nota: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    items: List[ItemSolicitudTransferenciaResponse]
