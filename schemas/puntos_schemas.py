"""
Schemas para el sistema de puntos.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum

class TipoMovimientoPuntosSchema(str, Enum):
    """Tipos de movimientos de puntos."""
    GANADOS = "GANADOS"
    USADOS = "USADOS"
    VENCIDOS = "VENCIDOS"
    AJUSTE = "AJUSTE"

class PuntosClienteBase(BaseModel):
    """Schema base para puntos de cliente."""
    cliente_id: int
    puntos_disponibles: int = Field(default=0, ge=0)
    puntos_totales_ganados: int = Field(default=0, ge=0)
    puntos_totales_usados: int = Field(default=0, ge=0)

class PuntosClienteCreate(PuntosClienteBase):
    """Schema para crear puntos de cliente."""
    pass

class PuntosClienteUpdate(BaseModel):
    """Schema para actualizar puntos de cliente."""
    puntos_disponibles: Optional[int] = Field(None, ge=0)
    puntos_totales_ganados: Optional[int] = Field(None, ge=0)
    puntos_totales_usados: Optional[int] = Field(None, ge=0)

class PuntosClienteResponse(PuntosClienteBase):
    """Schema de respuesta para puntos de cliente."""
    id: int
    
    class Config:
        from_attributes = True

class MovimientoPuntosBase(BaseModel):
    """Schema base para movimiento de puntos."""
    cliente_id: int
    tipo_movimiento: TipoMovimientoPuntosSchema
    puntos: int = Field(..., gt=0)
    descripcion: str
    pedido_id: Optional[int] = None

class MovimientoPuntosCreate(MovimientoPuntosBase):
    """Schema para crear movimiento de puntos."""
    pass

class MovimientoPuntosResponse(MovimientoPuntosBase):
    """Schema de respuesta para movimiento de puntos."""
    id: int
    fecha_movimiento: datetime
    
    class Config:
        from_attributes = True

class UsarPuntosRequest(BaseModel):
    """Schema para solicitud de usar puntos en pedido."""
    puntos_usar: int = Field(..., gt=0, description="Cantidad de puntos a usar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "puntos_usar": 50
            }
        }

class UsarPuntosResponse(BaseModel):
    """Schema de respuesta para uso de puntos."""
    exito: bool
    mensaje: str
    puntos_usados: int
    descuento_aplicado: Decimal
    puntos_disponibles_restantes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "exito": True,
                "mensaje": "Puntos usados exitosamente",
                "puntos_usados": 50,
                "descuento_aplicado": 500,
                "puntos_disponibles_restantes": 150
            }
        }

class EstadisticasPuntosResponse(BaseModel):
    """Schema para estadísticas del sistema de puntos."""
    total_ganados: int
    total_usados: int
    total_disponibles: int
    clientes_con_puntos: int
    movimientos_mes: List[dict]
    top_clientes: List[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_ganados": 15000,
                "total_usados": 5000,
                "total_disponibles": 10000,
                "clientes_con_puntos": 25,
                "movimientos_mes": [
                    {"tipo": "GANADOS", "total_puntos": 2000, "cantidad_movimientos": 15},
                    {"tipo": "USADOS", "total_puntos": 800, "cantidad_movimientos": 8}
                ],
                "top_clientes": [
                    {"nombre": "Juan Pérez", "email": "juan@email.com", "puntos_disponibles": 500}
                ]
            }
        }

class ValidacionPuntosRequest(BaseModel):
    """Schema para validar uso de puntos."""
    puntos_usar: int = Field(..., gt=0)
    total_pedido: Decimal = Field(..., gt=0)
    
class ValidacionPuntosResponse(BaseModel):
    """Schema de respuesta para validación de puntos."""
    valido: bool
    mensaje: str
    descuento_aplicable: Decimal
    puntos_maximos_usables: Optional[int] = None

# =======================================
# Schemas para estimación de puntos
# =======================================

class ItemParaEstimacionPuntos(BaseModel):
    """Item para estimar puntos."""
    producto_id: int = Field(..., gt=0)
    cantidad: float = Field(..., gt=0)

class EstimacionPuntosRequest(BaseModel):
    """Schema para solicitud de estimación de puntos."""
    items: List[ItemParaEstimacionPuntos] = Field(..., min_length=1)

class DetallePuntosPorCategoria(BaseModel):
    """Detalle de puntos por categoría."""
    categoria_nombre: str
    puntos_por_unidad: int
    cantidad: float
    puntos_subtotal: int

class EstimacionPuntosResponse(BaseModel):
    """Schema de respuesta para estimación de puntos."""
    total_puntos: int
    detalle_por_categoria: List[DetallePuntosPorCategoria]