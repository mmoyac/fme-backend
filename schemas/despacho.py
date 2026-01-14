"""
Schemas Pydantic para el sistema de despachos.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


class EstadoDespacho(str, Enum):
    """Estados del proceso de despacho."""
    ASIGNADO = "ASIGNADO"
    EN_PICKING = "EN_PICKING"
    LISTO_EMPAQUE = "LISTO_EMPAQUE"
    EN_RUTA = "EN_RUTA"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


# ============================================
# SCHEMAS DE PICKING ITEM
# ============================================

class PickingItemBase(BaseModel):
    """Base para items de picking."""
    item_pedido_id: int
    cantidad_solicitada: Optional[int] = None
    cantidad_pickeada: Optional[int] = None
    
    # Para cajas variables
    lote_codigo: Optional[str] = None
    peso_solicitado: Optional[Decimal] = None
    peso_real: Optional[Decimal] = None
    fecha_vencimiento: Optional[datetime] = None
    
    # Ubicación y proceso
    ubicacion_picking: Optional[str] = None
    codigo_barras_escaneado: Optional[str] = None
    notas_picking: Optional[str] = None
    completado: bool = False


class PickingItemCreate(PickingItemBase):
    """Schema para crear item de picking."""
    pass


class PickingItemUpdate(BaseModel):
    """Schema para actualizar item de picking."""
    cantidad_pickeada: Optional[int] = None
    peso_real: Optional[Decimal] = None
    ubicacion_picking: Optional[str] = None
    codigo_barras_escaneado: Optional[str] = None
    notas_picking: Optional[str] = None
    completado: Optional[bool] = None


class PickingItemResponse(PickingItemBase):
    """Schema de respuesta para item de picking."""
    id: int
    despacho_id: int
    usuario_picking_id: Optional[int] = None
    fecha_picking: Optional[datetime] = None
    
    # Información del producto (para mostrar en UI)
    producto_sku: Optional[str] = None
    producto_nombre: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS DE DESPACHO
# ============================================

class DespachoBase(BaseModel):
    """Base para despacho."""
    pedido_id: int
    despachador_user_id: int
    estado_despacho: EstadoDespacho = EstadoDespacho.ASIGNADO
    notas_despacho: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    hora_estimada_entrega: Optional[datetime] = None


class DespachoCreate(BaseModel):
    """Schema para crear despacho."""
    pedido_id: int
    despachador_user_id: int
    notas_despacho: Optional[str] = None
    hora_estimada_entrega: Optional[datetime] = None


class DespachoUpdate(BaseModel):
    """Schema para actualizar despacho."""
    estado_despacho: Optional[EstadoDespacho] = None
    notas_despacho: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    hora_estimada_entrega: Optional[datetime] = None


class DespachoResponse(DespachoBase):
    """Schema de respuesta para despacho."""
    id: int
    fecha_asignacion: datetime
    fecha_inicio_picking: Optional[datetime] = None
    fecha_fin_picking: Optional[datetime] = None
    fecha_inicio_ruta: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    
    # Información del despachador
    despachador_nombre: Optional[str] = None
    
    # Información del pedido
    pedido_numero: Optional[str] = None
    pedido_total: Optional[float] = None
    cliente_nombre: Optional[str] = None
    direccion_entrega: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DespachoConPickingItems(DespachoResponse):
    """Schema de despacho con items de picking incluidos."""
    picking_items: List[PickingItemResponse] = []


# ============================================
# SCHEMAS ESPECÍFICOS PARA PROCESOS
# ============================================

class AsignarDespachoRequest(BaseModel):
    """Request para asignar despacho."""
    despachador_user_id: int
    notas_despacho: Optional[str] = None
    hora_estimada_entrega: Optional[datetime] = None


class IniciarPickingRequest(BaseModel):
    """Request para iniciar proceso de picking."""
    ubicacion_actual: Optional[str] = None
    notas_despacho: Optional[str] = None


class CompletarPickingItemRequest(BaseModel):
    """Request para completar un item de picking."""
    cantidad_pickeada: Optional[int] = None
    peso_real: Optional[Decimal] = None
    ubicacion_picking: Optional[str] = None
    codigo_barras_escaneado: Optional[str] = None
    notas_picking: Optional[str] = None


class IniciarRutaRequest(BaseModel):
    """Request para iniciar ruta de entrega."""
    ubicacion_actual: str = Field(..., description="Coordenadas GPS de inicio")
    hora_estimada_entrega: Optional[datetime] = None


class ActualizarUbicacionRequest(BaseModel):
    """Request para actualizar ubicación en ruta."""
    ubicacion_actual: str = Field(..., description="Coordenadas GPS actuales")
    hora_estimada_entrega: Optional[datetime] = None


class ConfirmarEntregaRequest(BaseModel):
    """Request para confirmar entrega."""
    ubicacion_entrega: str = Field(..., description="Coordenadas GPS de entrega")
    notas_entrega: Optional[str] = None
    foto_entrega: Optional[str] = None  # Base64 encoded image


# ============================================
# SCHEMAS PARA NOTAS Y REPORTES
# ============================================

class NotaPickingResponse(BaseModel):
    """Schema para generar nota de picking."""
    despacho_id: int
    pedido_numero: str
    cliente_nombre: str
    direccion_entrega: str
    despachador_nombre: str
    fecha_asignacion: datetime
    items: List[dict]  # Lista de productos con cantidades y ubicaciones


class ResumenDespachoResponse(BaseModel):
    """Schema para resumen de despacho."""
    total_despachos: int
    en_picking: int
    listos_empaque: int
    en_ruta: int
    entregados_hoy: int
    tiempo_promedio_picking: Optional[float] = None  # minutos
    tiempo_promedio_entrega: Optional[float] = None  # minutos


# ============================================
# SCHEMAS PARA ESCANER MÓVIL
# ============================================

class EscanearCodigoBarrasRequest(BaseModel):
    """Request para escanear código de barras en picking."""
    despacho_id: int
    item_pedido_id: int
    codigo_barras: str
    ubicacion_actual: Optional[str] = None


class EscanearCodigoBarrasResponse(BaseModel):
    """Response del escaneo de código de barras."""
    picking_item_id: int
    producto_sku: str
    producto_nombre: str
    cantidad_solicitada: int
    cantidad_ya_pickeada: int
    cantidad_restante: int
    ubicacion_sugerida: Optional[str] = None
    es_caja_variable: bool = False
    lote_info: Optional[dict] = None  # Para cajas variables