"""
Schemas Pydantic para Pedido.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoPedido(str, Enum):
    """Estados posibles de un pedido."""
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


# ============================================
# Schemas para crear pedido desde frontend
# ============================================

class ItemPedidoCreateFrontend(BaseModel):
    """Item de pedido desde el carrito."""
    sku: str
    cantidad: int = Field(..., gt=0)


class PedidoCreateFrontend(BaseModel):
    """Schema para crear un Pedido desde el frontend (sin cliente registrado)."""
    # Datos del cliente
    cliente_nombre: str = Field(..., min_length=2, max_length=100)
    cliente_apellido: Optional[str] = Field(None, max_length=100)
    cliente_email: str = Field(..., min_length=5)
    cliente_telefono: str = Field(..., min_length=9, max_length=20)
    
    # Dirección de entrega
    direccion_entrega: str = Field(..., min_length=10, max_length=200)
    comuna: Optional[str] = Field(None, max_length=100)
    
    # Notas adicionales
    notas: Optional[str] = Field(None, max_length=500)
    
    # Items del pedido
    items: List[ItemPedidoCreateFrontend] = Field(..., min_length=1)


# ============================================
# Schemas base
# ============================================

class PedidoBase(BaseModel):
    """Schema base de Pedido."""
    cliente_id: int = Field(..., gt=0)
    local_id: int = Field(..., gt=0)


class PedidoCreate(PedidoBase):
    """Schema para crear un Pedido (uso interno)."""
    pass


class PedidoUpdate(BaseModel):
    """Schema para actualizar un Pedido."""
    estado: Optional[EstadoPedido] = None
    pagado: Optional[bool] = None
    notas_admin: Optional[str] = None
    local_despacho_id: Optional[int] = None


class PedidoResponse(BaseModel):
    """Schema de respuesta de Pedido."""
    id: int
    cliente_id: int
    local_id: int
    local_despacho_id: Optional[int] = None
    numero_pedido: Optional[str] = None
    fecha_pedido: datetime
    total: float
    estado: str
    pagado: bool
    inventario_descontado: bool = False
    notas: Optional[str] = None
    notas_admin: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PedidoConItems(BaseModel):
    """Schema de Pedido con sus items."""
    id: int
    cliente_id: int
    local_id: int
    local_despacho_id: Optional[int] = None
    numero_pedido: Optional[str] = None
    fecha_pedido: datetime
    total: float
    estado: str
    pagado: bool
    inventario_descontado: bool = False
    notas: Optional[str] = None
    notas_admin: Optional[str] = None
    items: List["ItemPedidoResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class PedidoConRelaciones(BaseModel):
    """Schema de Pedido con cliente e items."""
    id: int
    cliente_id: int
    local_id: int
    local_despacho_id: Optional[int] = None
    numero_pedido: Optional[str] = None
    fecha_pedido: datetime
    total: float
    estado: str
    pagado: bool
    inventario_descontado: bool = False
    notas: Optional[str] = None
    notas_admin: Optional[str] = None
    cliente: Optional["ClienteResponse"] = None
    items: List["ItemPedidoResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class PedidoConfirmacion(BaseModel):
    """Schema de respuesta después de crear un pedido."""
    pedido_id: int
    numero_pedido: str
    monto_total: float
    estado: str
    mensaje: str


# Importar para resolver la referencia circular
from .item_pedido import ItemPedidoResponse
from .cliente import ClienteResponse
PedidoConItems.model_rebuild()
PedidoConRelaciones.model_rebuild()
