"""
Schemas Pydantic para Caja y Turnos.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal
from database.models import TipoOperacionCaja


class EstadoTurnoCaja(str, Enum):
    """Estados posibles de un turno de caja."""
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"


# ============================================
# Schemas para Turno de Caja
# ============================================

class TurnoCajaBase(BaseModel):
    """Schema base para Turno de Caja."""
    local_id: int = Field(..., gt=0)
    monto_inicial: Decimal = Field(default=0.00, ge=0)
    observaciones_apertura: Optional[str] = None


class TurnoCajaCreate(TurnoCajaBase):
    """Schema para crear un turno de caja."""
    pass


class TurnoCajaClose(BaseModel):
    """Schema para cerrar un turno de caja."""
    efectivo_real: Decimal = Field(..., ge=0)
    observaciones_cierre: Optional[str] = None


class TurnoCajaResponse(TurnoCajaBase):
    """Schema de respuesta para Turno de Caja."""
    id: int
    vendedor_id: int
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    estado: EstadoTurnoCaja
    efectivo_esperado: Optional[Decimal] = None
    efectivo_real: Optional[Decimal] = None
    diferencia: Optional[Decimal] = None
    observaciones_cierre: Optional[str] = None
    
    # Información del vendedor
    vendedor_nombre: Optional[str] = None
    vendedor_email: Optional[str] = None
    
    # Información del local
    local_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Schemas para Operación de Caja
# ============================================

class OperacionCajaBase(BaseModel):
    """Schema base para Operación de Caja."""
    tipo_operacion: TipoOperacionCaja
    monto: Decimal = Field(..., gt=0)
    descripcion: str = Field(..., min_length=1, max_length=255)
    observaciones: Optional[str] = None
    medio_pago_id: Optional[int] = None


class OperacionCajaCreate(OperacionCajaBase):
    """Schema para crear una operación de caja."""
    pass


class OperacionCajaResponse(OperacionCajaBase):
    """Schema de respuesta para Operación de Caja."""
    id: int
    turno_caja_id: int
    fecha_operacion: datetime
    pedido_id: Optional[int] = None
    
    # Información del medio de pago
    medio_pago_codigo: Optional[str] = None
    medio_pago_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Schemas combinados
# ============================================

class TurnoCajaConOperaciones(TurnoCajaResponse):
    """Schema de Turno de Caja con sus operaciones."""
    operaciones: List[OperacionCajaResponse] = []

    model_config = ConfigDict(from_attributes=True)


class EstadoCajaVendedor(BaseModel):
    """Schema para el estado actual de caja de un vendedor."""
    vendedor_id: int
    vendedor_nombre: str
    tiene_caja_abierta: bool
    turno_activo: Optional[TurnoCajaResponse] = None
    
    # Totales del turno activo (si existe)
    total_ventas: Decimal = 0.00
    total_ingresos: Decimal = 0.00
    total_egresos: Decimal = 0.00
    efectivo_esperado: Decimal = 0.00

    model_config = ConfigDict(from_attributes=True)


class ResumenCajaLocal(BaseModel):
    """Schema para resumen de caja por local."""
    local_id: int
    local_nombre: str
    turnos_abiertos: int = 0
    vendedores_activos: List[str] = []
    total_efectivo_esperado: Decimal = 0.00
    total_ventas_dia: Decimal = 0.00

    model_config = ConfigDict(from_attributes=True)


class ReporteCajaDiario(BaseModel):
    """Schema para reporte diario de caja."""
    fecha: datetime
    vendedor_id: int
    vendedor_nombre: str
    turnos: List[TurnoCajaResponse] = []
    total_ventas: Decimal = 0.00
    total_ingresos: Decimal = 0.00
    total_egresos: Decimal = 0.00
    diferencias_totales: Decimal = 0.00

    model_config = ConfigDict(from_attributes=True)