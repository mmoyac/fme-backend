"""
Schemas Pydantic para tablas maestras del sistema de producción.
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


# ============================================
# TIPOS DE VENTA
# ============================================

class TipoVentaBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de venta")
    nombre: str = Field(..., description="Nombre del tipo de venta")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoVentaCreate(TipoVentaBase):
    pass


class TipoVentaUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoVenta(TipoVentaBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE PROVEEDOR
# ============================================

class TipoProveedorBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de proveedor")
    nombre: str = Field(..., description="Nombre del tipo de proveedor")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoProveedorCreate(TipoProveedorBase):
    pass


class TipoProveedorUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoProveedor(TipoProveedorBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# CATEGORÍAS DE PRODUCTO
# ============================================

class CategoriaProductoBase(BaseModel):
    codigo: str = Field(..., description="Código único de la categoría")
    nombre: str = Field(..., description="Nombre de la categoría")
    descripcion: Optional[str] = None
    puntos_fidelidad: int = Field(default=0, description="Puntos que otorga por venta")
    tipo_venta_id: Optional[int] = Field(None, description="ID del tipo de venta")
    activo: bool = True


class CategoriaProductoCreate(CategoriaProductoBase):
    pass


class CategoriaProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    puntos_fidelidad: Optional[int] = None
    tipo_venta_id: Optional[int] = None
    activo: Optional[bool] = None


class CategoriaProducto(CategoriaProductoBase):
    id: int
    tipo_venta: Optional[TipoVenta] = None

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE DOCUMENTO
# ============================================

class TipoDocumentoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de documento")
    nombre: str = Field(..., description="Nombre del tipo de documento")
    activo: bool = True


class TipoDocumentoCreate(TipoDocumentoBase):
    pass


class TipoDocumentoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = None


class TipoDocumento(TipoDocumentoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE PRODUCTO
# ============================================

class TipoProductoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo")
    nombre: str = Field(..., description="Nombre del tipo")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoProductoCreate(TipoProductoBase):
    pass


class TipoProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoProducto(TipoProductoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# UNIDADES DE MEDIDA
# ============================================

class UnidadMedidaBase(BaseModel):
    codigo: str = Field(..., description="Código único de la unidad")
    nombre: str = Field(..., description="Nombre completo")
    simbolo: str = Field(..., description="Símbolo (ej: kg, L, un)")
    tipo: Optional[str] = Field(None, description="CANTIDAD, PESO, VOLUMEN")
    factor_conversion: Optional[Decimal] = Field(None, description="Factor para convertir a unidad base")
    unidad_base_id: Optional[int] = Field(None, description="ID de la unidad base para conversiones")
    activo: bool = True


class UnidadMedidaCreate(UnidadMedidaBase):
    pass


class UnidadMedidaUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    tipo: Optional[str] = None
    factor_conversion: Optional[Decimal] = None
    unidad_base_id: Optional[int] = None
    activo: Optional[bool] = None


class UnidadMedida(UnidadMedidaBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# UNIDAD DE MEDIDA CON RELACIÓN
# ============================================

class UnidadMedidaConBase(UnidadMedida):
    """Unidad de medida con información de la unidad base."""
    unidad_base: Optional['UnidadMedida'] = None

    class Config:
        from_attributes = True


# ============================================
# MEDIOS DE PAGO
# ============================================

class MedioPagoBase(BaseModel):
    codigo: str = Field(..., description="Código único del medio de pago")
    nombre: str = Field(..., description="Nombre del medio de pago")
    descripcion: Optional[str] = None
    permite_cheque: bool = Field(default=False, description="Si permite ingresar datos de cheque")
    es_contado: bool = Field(default=False, description="Si este medio es al contado (aplica descuento contado en preventas)")
    activo: bool = True


class MedioPagoCreate(MedioPagoBase):
    pass


class MedioPagoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permite_cheque: Optional[bool] = None
    es_contado: Optional[bool] = None
    activo: Optional[bool] = None


class MedioPago(MedioPagoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# ESTADOS DE CHEQUE
# ============================================

class EstadoChequeBase(BaseModel):
    codigo: str = Field(..., description="Código único del estado de cheque")
    nombre: str = Field(..., description="Nombre del estado")
    descripcion: Optional[str] = None
    es_final: bool = Field(default=False, description="Si es un estado final")
    activo: bool = True


class EstadoChequeCreate(EstadoChequeBase):
    pass


class EstadoChequeUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_final: Optional[bool] = None
    activo: Optional[bool] = None


class EstadoCheque(EstadoChequeBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# BANCOS
# ============================================

class BancoBase(BaseModel):
    codigo: str = Field(..., description="Código único del banco")
    nombre: str = Field(..., description="Nombre del banco")
    nombre_corto: Optional[str] = Field(None, description="Nombre corto del banco")
    activo: bool = True


class BancoCreate(BancoBase):
    pass


class BancoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    nombre_corto: Optional[str] = None
    activo: Optional[bool] = None


class Banco(BancoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE VEHÍCULO
# ============================================

class TipoVehiculoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de vehículo")
    nombre: str = Field(..., description="Nombre del tipo de vehículo")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoVehiculoCreate(TipoVehiculoBase):
    pass


class TipoVehiculoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoVehiculo(TipoVehiculoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# ESTADOS DE ENROLAMIENTO
# ============================================

class EstadoEnrolamientoBase(BaseModel):
    codigo: str = Field(..., description="Código único del estado")
    nombre: str = Field(..., description="Nombre del estado")
    descripcion: Optional[str] = None
    activo: bool = True


class EstadoEnrolamientoCreate(EstadoEnrolamientoBase):
    pass


class EstadoEnrolamientoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class EstadoEnrolamiento(EstadoEnrolamientoBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# UBICACIONES
# ============================================

class UbicacionBase(BaseModel):
    codigo: str = Field(..., description="Código único de la ubicación (P1-A-01)")
    nombre: str = Field(..., description="Nombre de la ubicación")
    descripcion: Optional[str] = None
    capacidad_maxima: int = Field(default=0, description="Número máximo de cajas")
    activo: bool = True


class UbicacionCreate(UbicacionBase):
    pass


class UbicacionUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    capacidad_maxima: Optional[int] = None
    activo: Optional[bool] = None


class Ubicacion(UbicacionBase):
    id: int

    class Config:
        from_attributes = True


# ============================================
# TIPOS DE DOCUMENTO TRIBUTARIO
# ============================================

class TipoDocumentoBase(BaseModel):
    codigo: str = Field(..., description="Código único del tipo de documento")
    nombre: str = Field(..., description="Nombre del tipo de documento")
    descripcion: Optional[str] = None
    activo: bool = True


class TipoDocumentoCreate(TipoDocumentoBase):
    pass


class TipoDocumentoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class TipoDocumento(TipoDocumentoBase):
    id: int

    class Config:
        from_attributes = True
