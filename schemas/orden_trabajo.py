"""
Schemas Pydantic para Órdenes de Trabajo: TipoOT, EstadoCotizacion, EstadoOT, OtEtapaTipo, OrdenTrabajo.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# --------------------------------------------------
# TipoOT
# --------------------------------------------------

class TipoOTBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    activo: bool = Field(default=True)


class TipoOTCreate(TipoOTBase):
    pass


class TipoOTUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None


class TipoOTResponse(TipoOTBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# EstadoCotizacion
# --------------------------------------------------

class EstadoCotizacionBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    color: str = Field(default='gray-500', max_length=20)
    orden: int = Field(default=0)
    es_final: bool = Field(default=False)
    activo: bool = Field(default=True)


class EstadoCotizacionResponse(EstadoCotizacionBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# EstadoOT
# --------------------------------------------------

class EstadoOTBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    color: str = Field(default='gray-500', max_length=20)
    orden: int = Field(default=0)
    es_final: bool = Field(default=False)
    activo: bool = Field(default=True)


class EstadoOTResponse(EstadoOTBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# OtEtapaTipo
# --------------------------------------------------

class TipoOTBasico(BaseModel):
    id: int
    codigo: str
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class OtEtapaTipoBase(BaseModel):
    tipo_ot_id: int = Field(..., description="ID del tipo de OT (OP, OS, ...)")
    nombre: str = Field(..., min_length=1, max_length=100)
    orden: int = Field(default=0)
    es_etapa_final: bool = Field(default=False)
    color: Optional[str] = Field(None, max_length=10, description="Color hex para UI: '#22c55e'")
    activo: bool = Field(default=True)


class OtEtapaTipoCreate(OtEtapaTipoBase):
    pass


class OtEtapaTipoUpdate(BaseModel):
    tipo_ot_id: Optional[int] = None
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    orden: Optional[int] = None
    es_etapa_final: Optional[bool] = None
    color: Optional[str] = Field(None, max_length=10)
    activo: Optional[bool] = None


class OtEtapaTipoResponse(OtEtapaTipoBase):
    id: int
    tenant_id: int
    tipo_ot: TipoOTBasico
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# Schemas embebidos para OT
# --------------------------------------------------

class ProductoBasico(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)


class UnidadMedidaBasica(BaseModel):
    id: int
    nombre: str
    abreviacion: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class LocalBasico(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)


class UsuarioBasico(BaseModel):
    id: int
    nombre_completo: Optional[str] = None
    email: str
    model_config = ConfigDict(from_attributes=True)


class EstadoOTBasico(BaseModel):
    id: int
    codigo: str
    nombre: str
    color: str
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# OtItem
# --------------------------------------------------

class OtItemCreate(BaseModel):
    producto_id: int
    unidad_medida_id: Optional[int] = None
    cantidad: float = Field(..., gt=0)
    notas: Optional[str] = None


class OtItemUpdate(BaseModel):
    cantidad_ejecutada: Optional[float] = Field(None, ge=0)
    notas: Optional[str] = None


class OtItemResponse(BaseModel):
    id: int
    producto_id: int
    producto: ProductoBasico
    unidad_medida: Optional[UnidadMedidaBasica] = None
    cantidad: float
    cantidad_ejecutada: Optional[float] = None
    notas: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# OtLog
# --------------------------------------------------

class OtLogResponse(BaseModel):
    id: int
    accion: str
    detalle: Optional[str] = None
    etapa: Optional[OtEtapaTipoResponse] = None
    usuario: Optional[UsuarioBasico] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# OrdenTrabajo
# --------------------------------------------------

class OrdenTrabajoCreate(BaseModel):
    tipo_ot_id: int
    local_id: int
    pedido_id: Optional[int] = None
    cotizacion_id: Optional[int] = None
    fecha_programada: Optional[datetime] = None
    notas: Optional[str] = None
    items: List[OtItemCreate]


class OrdenTrabajoUpdate(BaseModel):
    local_id: Optional[int] = None
    fecha_programada: Optional[datetime] = None
    notas: Optional[str] = None


class OrdenTrabajoResponse(BaseModel):
    id: int
    tenant_id: int
    numero_ot: str
    tipo_ot: TipoOTBasico
    estado_ot: EstadoOTBasico
    etapa_actual: Optional[OtEtapaTipoResponse] = None
    local: LocalBasico
    pedido_id: Optional[int] = None
    cotizacion_id: Optional[int] = None
    op_id: Optional[int] = None
    fecha_programada: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    notas: Optional[str] = None
    creado_por: Optional[UsuarioBasico] = None
    items: List[OtItemResponse] = []
    log: List[OtLogResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrdenTrabajoListResponse(BaseModel):
    id: int
    numero_ot: str
    tipo_ot: TipoOTBasico
    estado_ot: EstadoOTBasico
    etapa_actual: Optional[OtEtapaTipoResponse] = None
    local: LocalBasico
    pedido_id: Optional[int] = None
    cotizacion_id: Optional[int] = None
    fecha_programada: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AvanzarEtapaRequest(BaseModel):
    etapa_id: int = Field(..., description="ID de la nueva etapa")
    detalle: Optional[str] = None


class CerrarOTRequest(BaseModel):
    detalle: Optional[str] = None
    items_ejecutados: Optional[List[OtItemUpdate]] = None  # cantidades ejecutadas opcionales
