
from pydantic import BaseModel, condecimal
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Detalle ---
class DetalleOrdenCreate(BaseModel):
    producto_id: int
    cantidad: Decimal
    unidad_medida_id: int

class DetalleOrdenRead(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    unidad_medida_id: int
    cantidad_programada: Decimal
    cantidad_producida: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

# --- Orden ---
class OrdenProduccionCreate(BaseModel):
    local_id: int
    fecha_programada: datetime
    notas: Optional[str] = None
    detalles: List[DetalleOrdenCreate]

class OrdenProduccionRead(BaseModel):
    id: int
    local_id: int
    fecha_programada: datetime
    fecha_creacion: datetime
    fecha_finalizacion: Optional[datetime] = None
    estado: str
    notas: Optional[str] = None
    detalles: List[DetalleOrdenRead]

    class Config:
        from_attributes = True

# --- Confirmación de Finalización (Ajustes Reales) ---

class AjusteProduccion(BaseModel):
    detalle_id: int
    cantidad_producida_real: Decimal

class AjusteConsumo(BaseModel):
    producto_id: int
    cantidad_consumida_real: Decimal
    
class ConfirmacionFinalizacion(BaseModel):
    detalles_ajustes: List[AjusteProduccion] = []
    insumos_ajustes: List[AjusteConsumo] = [] # Consumo real de MP
    notas_finalizacion: Optional[str] = None
