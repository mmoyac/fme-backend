
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Usuario (trazabilidad) ---
class UsuarioRef(BaseModel):
    id: int
    nombre_completo: Optional[str] = None
    email: str

    class Config:
        from_attributes = True

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
    motivo_diferencia: Optional[str] = None

    @computed_field
    @property
    def diferencia(self) -> Optional[Decimal]:
        """producida - programada (negativo = se produjo menos). None si la OP no está finalizada."""
        if self.cantidad_producida is None:
            return None
        return self.cantidad_producida - self.cantidad_programada

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
    solicitado_por: Optional[UsuarioRef] = None
    producido_por: Optional[UsuarioRef] = None

    class Config:
        from_attributes = True

# --- Confirmación de Finalización (Ajustes Reales) ---

class AjusteProduccion(BaseModel):
    detalle_id: int
    cantidad_producida_real: Decimal = Field(ge=0)
    motivo_diferencia: Optional[str] = Field(default=None, max_length=500)

class AjusteConsumo(BaseModel):
    producto_id: int
    cantidad_consumida_real: Decimal
    
class ConfirmacionFinalizacion(BaseModel):
    detalles_ajustes: List[AjusteProduccion] = []
    insumos_ajustes: List[AjusteConsumo] = [] # Consumo real de MP
    notas_finalizacion: Optional[str] = None


class EdicionCantidadDetalle(BaseModel):
    detalle_id: int
    cantidad_programada: Decimal = Field(gt=0)


class EdicionCantidadesOrden(BaseModel):
    """Editar cantidades programadas de una OP PLANIFICADA (solo admin)."""
    detalles: List[EdicionCantidadDetalle]
    motivo: Optional[str] = Field(default=None, max_length=500)
