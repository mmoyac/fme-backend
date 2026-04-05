"""
Schemas Pydantic para Cotizaciones.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, date


# --------------------------------------------------
# Schemas embebidos (referencias básicas)
# --------------------------------------------------

class ClienteBasico(BaseModel):
    id: int
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EstadoCotizacionBasico(BaseModel):
    id: int
    codigo: str
    nombre: str
    color: str
    model_config = ConfigDict(from_attributes=True)


class CanalVentaBasico(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)


class UsuarioBasico(BaseModel):
    id: int
    nombre_completo: Optional[str] = None
    email: str
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# Item de cotización (dentro del JSON)
# --------------------------------------------------

class ItemCotizacion(BaseModel):
    producto_id: int
    nombre: str
    cantidad: float = Field(..., gt=0)
    precio_unitario: float = Field(..., ge=0)
    subtotal: float = Field(..., ge=0)


# --------------------------------------------------
# CotizacionVersion
# --------------------------------------------------

class CotizacionVersionCreate(BaseModel):
    items: List[ItemCotizacion]
    monto_total: float = Field(..., ge=0)
    motivo_cambio: Optional[str] = None


class CotizacionVersionResponse(BaseModel):
    id: int
    cotizacion_id: int
    numero_version: int
    items: List[Any]
    monto_total: float
    motivo_cambio: Optional[str] = None
    es_version_aceptada: bool
    creado_por: Optional[UsuarioBasico] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# CotizacionLog
# --------------------------------------------------

class CotizacionLogResponse(BaseModel):
    id: int
    accion: str
    detalle: Optional[str] = None
    version_id: Optional[int] = None
    usuario: Optional[UsuarioBasico] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# Cotizacion
# --------------------------------------------------

class CotizacionCreate(BaseModel):
    cliente_id: int
    canal_venta_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    notas: Optional[str] = None
    items: List[ItemCotizacion]                       # Items de la versión inicial
    monto_total: float = Field(..., ge=0)


class CotizacionUpdate(BaseModel):
    canal_venta_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    notas: Optional[str] = None


class CotizacionResponse(BaseModel):
    id: int
    tenant_id: int
    numero_cotizacion: str
    cliente: ClienteBasico
    canal_venta: Optional[CanalVentaBasico] = None
    estado_cotizacion: EstadoCotizacionBasico
    fecha_vencimiento: Optional[date] = None
    notas: Optional[str] = None
    version_activa: Optional[CotizacionVersionResponse] = None
    versiones: List[CotizacionVersionResponse] = []
    log: List[CotizacionLogResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CotizacionListResponse(BaseModel):
    """Schema liviano para listado (sin versiones ni log completo)."""
    id: int
    numero_cotizacion: str
    cliente: ClienteBasico
    canal_venta: Optional[CanalVentaBasico] = None
    estado_cotizacion: EstadoCotizacionBasico
    fecha_vencimiento: Optional[date] = None
    monto_total: Optional[float] = None              # Viene de version_activa
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
