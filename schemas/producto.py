"""
Schemas Pydantic para Producto.
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class ProductoBase(BaseModel):
    """Schema base de Producto."""
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: str = Field(..., min_length=1, max_length=100)
    imagen_url: Optional[str] = None
    codigo_barra: Optional[str] = Field(None, max_length=50)
    categoria_id: int
    tipo_producto_id: int
    unidad_medida_id: int
    precio_compra: Optional[Decimal] = None
    costo_fabricacion: Optional[Decimal] = None
    peso_bruto: Optional[Decimal] = Field(None, ge=0, description="Peso bruto en kg (producto + empaque). Para asignación de vehículos en delivery.")
    es_vendible: bool = True
    es_vendible_web: bool = False
    es_ingrediente: bool = False
    tiene_receta: bool = False
    activo: bool = True
    stock_minimo: Optional[int] = 0
    stock_critico: Optional[int] = 0
    precio_incluye_iva: bool = True  # True: precio ya tiene IVA incluido. False: precio es neto, se agrega 19%
    descuento_contado: Optional[Decimal] = Field(None, ge=0, le=100, description="% de descuento aplicado cuando el pago es al contado")


class ProductoCreate(ProductoBase):
    """Schema para crear un Producto."""
    pass


class ProductoUpdate(BaseModel):
    """Schema para actualizar un Producto."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    imagen_url: Optional[str] = None
    codigo_barra: Optional[str] = Field(None, max_length=50)
    categoria_id: Optional[int] = None
    tipo_producto_id: Optional[int] = None
    unidad_medida_id: Optional[int] = None
    precio_compra: Optional[Decimal] = None
    costo_fabricacion: Optional[Decimal] = None
    peso_bruto: Optional[Decimal] = Field(None, ge=0, description="Peso bruto en kg (producto + empaque). Para asignación de vehículos en delivery.")
    es_vendible: Optional[bool] = None
    es_vendible_web: Optional[bool] = None
    es_ingrediente: Optional[bool] = None
    tiene_receta: Optional[bool] = None
    activo: Optional[bool] = None
    stock_minimo: Optional[int] = None
    stock_critico: Optional[int] = None
    precio_incluye_iva: Optional[bool] = None
    descuento_contado: Optional[Decimal] = None


class ProductoResponse(ProductoBase):
    """Schema de respuesta de Producto."""
    id: int
    stock_actual: int = 0  # Campo calculado para visualización
    # Información de categoría
    categoria_nombre: Optional[str] = None
    categoria_puntos_fidelidad: Optional[int] = None
    # Información de tipo de venta (peso vs cantidad)
    tipo_venta_codigo: Optional[str] = None  # UNITARIO, PESO_SUELTO, CAJA_VARIABLE
    tipo_venta_nombre: Optional[str] = None
    # Unidad de medida simbólica (ej: kg, un, l)
    unidad_medida_simbolo: Optional[str] = None

    class Config:
        from_attributes = True
