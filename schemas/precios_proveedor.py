"""
Schemas para la gestión de precios por proveedor
Para productos de caja variable (carnes)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class PrecioProveedorBase(BaseModel):
    precio_kg: Decimal = Field(..., ge=0, description="Precio por kilogramo")
    notas: Optional[str] = Field(None, description="Notas sobre el precio")
    activo: bool = Field(default=True, description="Si el precio está activo")


class PrecioProveedorCreate(PrecioProveedorBase):
    producto_id: int = Field(..., description="ID del producto")
    proveedor_id: int = Field(..., description="ID del proveedor")


class PrecioProveedorUpdate(BaseModel):
    precio_kg: Optional[Decimal] = Field(None, ge=0, description="Nuevo precio por kilogramo")
    notas: Optional[str] = Field(None, description="Notas sobre el precio")
    activo: Optional[bool] = Field(None, description="Estado del precio")


class PrecioProveedorResponse(PrecioProveedorBase):
    id: int
    producto_id: int
    proveedor_id: int
    fecha_vigencia: datetime
    
    class Config:
        from_attributes = True


class PrecioProveedorConDetalles(PrecioProveedorResponse):
    """Precio con información de producto y proveedor."""
    producto_nombre: str
    producto_sku: str
    proveedor_nombre: str
    proveedor_rut: str
    
    class Config:
        from_attributes = True


class ProductoPreciosProveedores(BaseModel):
    """Producto con todos sus precios por proveedor."""
    id: int
    nombre: str
    sku: str
    precios_proveedores: List[PrecioProveedorConDetalles] = []
    
    class Config:
        from_attributes = True


class ProveedorPreciosProductos(BaseModel):
    """Proveedor con todos sus precios por producto."""
    id: int
    nombre: str
    rut: str
    precios_productos: List[PrecioProveedorConDetalles] = []
    
    class Config:
        from_attributes = True