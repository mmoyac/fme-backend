"""
Schemas Pydantic para el sistema de enrolamiento y trazabilidad de lotes.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Importar esquemas ya existentes
from .maestras import TipoVehiculo, EstadoEnrolamiento, Ubicacion
from .auth import User


# ============================================
# ESQUEMAS AUXILIARES PARA OBJETOS RELACIONADOS
# ============================================

class ProveedorSimple(BaseModel):
    """Esquema simple para proveedor en respuestas."""
    id: int
    nombre: str
    rut: Optional[str] = None
    activo: bool
    
    class Config:
        from_attributes = True


class ProductoSimple(BaseModel):
    """Esquema simple para producto en respuestas."""
    id: int
    nombre: str
    sku: str
    descripcion: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# ENROLAMIENTO DE VEHÍCULOS
# ============================================

class EnrolamientoBase(BaseModel):
    patente: str = Field(..., description="Patente del vehículo")
    chofer: str = Field(..., description="Nombre del chofer")
    numero_documento: str = Field(..., description="Número de guía o factura")
    notas: Optional[str] = None


class EnrolamientoCreate(EnrolamientoBase):
    tipo_vehiculo_id: int = Field(..., description="ID del tipo de vehículo")
    proveedor_id: int = Field(..., description="ID del proveedor (solo tipo CARNES)")
    estado_id: int = Field(..., description="ID del estado inicial")
    usuario_registro_id: int = Field(..., description="ID del usuario que registra")


class EnrolamientoUpdate(BaseModel):
    patente: Optional[str] = None
    chofer: Optional[str] = None
    numero_documento: Optional[str] = None
    tipo_vehiculo_id: Optional[int] = None
    proveedor_id: Optional[int] = None
    estado_id: Optional[int] = None
    fecha_termino: Optional[datetime] = None
    notas: Optional[str] = None


class EnrolamientoResponse(EnrolamientoBase):
    id: int
    tipo_vehiculo_id: int
    proveedor_id: int
    estado_id: int
    usuario_registro_id: int
    fecha_inicio: datetime
    fecha_termino: Optional[datetime]
    
    # Datos relacionados usando esquemas correctos
    tipo_vehiculo: Optional[TipoVehiculo] = None
    proveedor: Optional[ProveedorSimple] = None
    estado: Optional[EstadoEnrolamiento] = None
    usuario_registro: Optional[User] = None

    class Config:
        from_attributes = True


class EnrolamientoList(BaseModel):
    """Lista de enrolamientos con datos básicos."""
    id: int
    patente: str
    chofer: str
    numero_documento: str
    fecha_inicio: datetime
    fecha_termino: Optional[datetime]
    tipo_vehiculo_nombre: str
    proveedor_nombre: str
    estado_nombre: str
    usuario_registro_nombre: str

    class Config:
        from_attributes = True


# ============================================
# LOTES INDIVIDUALES
# ============================================

class LoteBase(BaseModel):
    peso_original: Decimal = Field(..., description="Peso extraído de la etiqueta original")
    peso_actual: Decimal = Field(..., description="Peso actual del lote")
    fecha_vencimiento: datetime = Field(..., description="Fecha de vencimiento")
    fecha_fabricacion: Optional[datetime] = None
    qr_original: Optional[str] = None
    lote_proveedor: Optional[str] = Field(None, description="Número de lote del proveedor")
    foto_etiqueta: Optional[str] = None


class LoteCreate(LoteBase):
    enrolamiento_id: int = Field(..., description="ID del enrolamiento")
    producto_id: int = Field(..., description="ID del producto")
    ubicacion_id: int = Field(..., description="ID de la ubicación en almacén")
    codigo_lote: str = Field(..., description="Código único del lote")
    qr_propio: str = Field(..., description="QR generado por el sistema")


class LoteUpdate(BaseModel):
    peso_actual: Optional[Decimal] = None
    fecha_vencimiento: Optional[datetime] = None
    fecha_fabricacion: Optional[datetime] = None
    ubicacion_id: Optional[int] = None
    qr_original: Optional[str] = None
    lote_proveedor: Optional[str] = None
    foto_etiqueta: Optional[str] = None
    disponible_venta: Optional[bool] = None
    vendido: Optional[bool] = None


class LoteResponse(LoteBase):
    id: int
    enrolamiento_id: int
    producto_id: int
    ubicacion_id: int
    codigo_lote: str
    qr_propio: str
    disponible_venta: bool
    vendido: bool
    fecha_registro: datetime
    
    # Datos relacionados usando esquemas correctos
    enrolamiento: Optional['EnrolamientoResponse'] = None
    producto: Optional[ProductoSimple] = None
    ubicacion: Optional[Ubicacion] = None

    class Config:
        from_attributes = True


class LoteList(BaseModel):
    """Lista de lotes con datos básicos para grillas."""
    id: int
    codigo_lote: str
    qr_propio: str
    qr_original: Optional[str] = None  # QR de la etiqueta original
    lote_proveedor: Optional[str] = None  # Lote del proveedor
    peso_original: float
    peso_actual: float
    fecha_vencimiento: datetime
    disponible_venta: bool
    vendido: bool
    fecha_registro: datetime
    producto_nombre: str
    ubicacion_codigo: str
    enrolamiento_patente: str

    @validator('peso_original', 'peso_actual', pre=True)
    def decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

    class Config:
        from_attributes = True


# ============================================
# CONSULTAS Y FILTROS
# ============================================

class FiltroEnrolamiento(BaseModel):
    """Filtros para búsqueda de enrolamientos."""
    estado_id: Optional[int] = None
    proveedor_id: Optional[int] = None
    tipo_vehiculo_id: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    patente: Optional[str] = None
    numero_documento: Optional[str] = None


class FiltroLote(BaseModel):
    """Filtros para búsqueda de lotes."""
    enrolamiento_id: Optional[int] = None
    producto_id: Optional[int] = None
    ubicacion_id: Optional[int] = None
    disponible_venta: Optional[bool] = None
    vendido: Optional[bool] = None
    fecha_vencimiento_desde: Optional[datetime] = None
    fecha_vencimiento_hasta: Optional[datetime] = None


# ============================================
# RESPUESTAS ESPECIALES
# ============================================

class EstadisticasEnrolamiento(BaseModel):
    """Estadísticas del sistema de enrolamiento."""
    total_enrolamientos: int
    pendientes: int
    en_proceso: int
    finalizados: int
    total_lotes: int
    lotes_disponibles: int
    lotes_vendidos: int
    cajas_por_mes: int

    class Config:
        from_attributes = True


# Resolver referencias forward
LoteResponse.model_rebuild()


class ProveedoresCarne(BaseModel):
    """Lista de proveedores filtrados por tipo CARNES."""
    id: int
    nombre: str
    rut: str
    telefono: Optional[str]
    activo: bool

    class Config:
        from_attributes = True