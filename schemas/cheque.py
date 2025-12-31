"""
Schemas Pydantic para gestión de cheques.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .maestras import EstadoCheque


# ============================================
# SCHEMAS BASE PARA CHEQUE
# ============================================

class ChequeBase(BaseModel):
    numero_cheque: str = Field(..., description="Número del cheque")
    banco_id: int = Field(..., description="ID del banco emisor")
    monto: Decimal = Field(..., description="Monto del cheque")
    fecha_emision: datetime = Field(..., description="Fecha de emisión")
    fecha_vencimiento: datetime = Field(..., description="Fecha de vencimiento")
    librador_nombre: str = Field(..., description="Nombre del librador")
    librador_rut: Optional[str] = Field(None, description="RUT del librador")
    observaciones: Optional[str] = None


class ChequeCreate(ChequeBase):
    pedido_id: int = Field(..., description="ID del pedido asociado")
    estado_id: Optional[int] = Field(default=None, description="ID del estado inicial (por defecto PENDIENTE)")


class ChequeUpdate(BaseModel):
    estado_id: Optional[int] = None
    fecha_deposito: Optional[datetime] = None
    fecha_cobro: Optional[datetime] = None
    observaciones: Optional[str] = None


class Cheque(ChequeBase):
    id: int
    pedido_id: int
    estado_id: int
    fecha_recepcion: datetime
    fecha_deposito: Optional[datetime] = None
    fecha_cobro: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# SCHEMAS CON RELACIONES
# ============================================

class BancoResponse(BaseModel):
    """Schema simplificado para banco en respuestas."""
    id: int
    codigo: str
    nombre: str
    nombre_corto: Optional[str] = None

    class Config:
        from_attributes = True


class ChequeConBancoYEstado(Cheque):
    """Cheque con información del banco y estado."""
    banco_rel: BancoResponse
    estado: EstadoCheque

    class Config:
        from_attributes = True

# Actualizar referencias circulares
ChequeConBancoYEstado.model_rebuild()


class ChequeConEstado(ChequeConBancoYEstado):
    """Compatibilidad hacia atrás - usar ChequeConBancoYEstado."""
    pass


# ============================================
# SCHEMAS PARA GESTIÓN DE CHEQUES EN PEDIDOS
# ============================================

class PedidoChequeCreate(BaseModel):
    """Schema para crear múltiples cheques al crear/editar un pedido."""
    cheques: list[ChequeCreate] = Field(default_factory=list, description="Lista de cheques del pedido")


class ResumenChequesPedido(BaseModel):
    """Resumen del estado de cheques de un pedido."""
    total_cheques: int
    monto_total_cheques: Decimal
    cheques_pendientes: int
    cheques_cobrados: int
    cheques_rechazados: int
    todos_cobrados: bool = Field(description="True si todos los cheques están cobrados")
    
    
class PedidoConCheques(BaseModel):
    """Pedido con información detallada de cheques."""
    pedido_id: int
    numero_pedido: str
    monto_total: Decimal
    es_pagado: bool
    medio_pago_codigo: Optional[str] = None
    resumen_cheques: Optional[ResumenChequesPedido] = None
    cheques: list[ChequeConEstado] = Field(default_factory=list)

    class Config:
        from_attributes = True