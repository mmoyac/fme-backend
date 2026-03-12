from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class ComisionOut(BaseModel):
    id: int
    vendedor_id: int
    vendedor_nombre: Optional[str] = None
    pedido_id: int
    numero_pedido: str
    porcentaje: float
    monto_bruto: float
    monto_neto: float
    monto_comision: float
    periodo: str
    fecha_pedido: Optional[datetime] = None
    fecha_generacion: datetime
    estado: str
    liquidacion_id: Optional[int] = None

    class Config:
        from_attributes = True


class LiquidacionCreate(BaseModel):
    vendedor_id: int
    periodo: str  # "2026-03"
    notas: Optional[str] = None


class LiquidacionOut(BaseModel):
    id: int
    vendedor_id: int
    vendedor_nombre: Optional[str] = None
    periodo: str
    fecha_inicio: date
    fecha_fin: date
    fecha_pago_prevista: date
    total_ventas_neto: float
    total_comision: float
    cantidad_pedidos: int
    estado: str
    notas: Optional[str] = None
    fecha_creacion: datetime
    fecha_pago_real: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumenVendedorPeriodo(BaseModel):
    vendedor_id: int
    vendedor_nombre: Optional[str] = None
    porcentaje_comision: Optional[float] = None
    periodo: str
    total_ventas_neto: float
    total_comision: float
    cantidad_pedidos: int
    tiene_liquidacion: bool
