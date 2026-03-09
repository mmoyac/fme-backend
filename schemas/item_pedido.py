"""
Schemas Pydantic para ItemPedido.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ItemPedidoBase(BaseModel):
    """Schema base de ItemPedido."""
    pedido_id: int = Field(..., gt=0)
    producto_id: int = Field(..., gt=0)
    cantidad: float = Field(..., gt=0)  # Cambiado a float para soportar decimales
    precio_unitario_venta: float = Field(..., gt=0)
    local_cliente_id: Optional[int] = None  # Local de despacho del cliente para este ítem


class ItemPedidoCreate(BaseModel):
    """Schema para crear un ItemPedido (sin pedido_id, se asigna automáticamente)."""
    producto_id: int = Field(..., gt=0)
    cantidad: float = Field(..., gt=0)  # Cambiado a float para soportar decimales
    precio_unitario_venta: float = Field(..., gt=0)
    local_cliente_id: Optional[int] = None  # Local de despacho del cliente para este ítem


class ItemPedidoUpdate(BaseModel):
    """Schema para actualizar un ItemPedido."""
    cantidad: Optional[float] = Field(None, gt=0)  # Cambiado a float para soportar decimales
    precio_unitario_venta: Optional[float] = Field(None, gt=0)


class ItemPedidoResponse(ItemPedidoBase):
    """Schema de respuesta de ItemPedido."""
    id: int
    producto: Optional["ProductoSimple"] = None
    producto_nombre: Optional[str] = None
    peso_total_kg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ProductoSimple(BaseModel):
    """Schema simplificado de Producto para los items."""
    id: int
    nombre: str
    sku: str

    model_config = ConfigDict(from_attributes=True)


# Resolver referencia circular
ItemPedidoResponse.model_rebuild()
