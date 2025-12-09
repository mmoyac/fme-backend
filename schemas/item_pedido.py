"""
Schemas Pydantic para ItemPedido.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ItemPedidoBase(BaseModel):
    """Schema base de ItemPedido."""
    pedido_id: int = Field(..., gt=0)
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    precio_unitario_venta: float = Field(..., gt=0)


class ItemPedidoCreate(BaseModel):
    """Schema para crear un ItemPedido (sin pedido_id, se asigna automáticamente)."""
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    precio_unitario_venta: float = Field(..., gt=0)


class ItemPedidoUpdate(BaseModel):
    """Schema para actualizar un ItemPedido."""
    cantidad: Optional[int] = Field(None, gt=0)
    precio_unitario_venta: Optional[float] = Field(None, gt=0)


class ItemPedidoResponse(ItemPedidoBase):
    """Schema de respuesta de ItemPedido."""
    id: int
    producto: Optional["ProductoSimple"] = None

    model_config = ConfigDict(from_attributes=True)


class ProductoSimple(BaseModel):
    """Schema simplificado de Producto para los items."""
    id: int
    nombre: str
    sku: str

    model_config = ConfigDict(from_attributes=True)


# Resolver referencia circular
ItemPedidoResponse.model_rebuild()
