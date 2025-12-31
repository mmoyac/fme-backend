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
    direccion_entrega: str = Field(..., min_length=5, max_length=200)
    comuna: Optional[str] = Field(None, max_length=100)
    
    # Notas adicionales
    notas: Optional[str] = Field(None, max_length=500)
    
    # Medio de pago (opcional, por defecto MERCADOPAGO para frontend)
    medio_pago_codigo: Optional[str] = Field(default="MERCADOPAGO", description="Código del medio de pago")
    
    # Puntos a usar (opcional)
    puntos_usar: Optional[int] = Field(default=0, ge=0, description="Puntos a usar para descuento")
    
    # Items del pedido
    items: List[ItemPedidoCreateFrontend] = Field(..., min_length=1)


# ============================================
# Schemas para crear pedido desde backoffice
# ============================================

class ItemPedidoCreateBackoffice(BaseModel):
    """Item de pedido desde el backoffice."""
    sku: str
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)
    precio_unitario_venta: float = Field(..., gt=0)


class PedidoCreateBackoffice(BaseModel):
    """Schema para crear un Pedido desde el backoffice."""
    cliente_id: int = Field(..., gt=0)
    cliente_nombre: str
    cliente_email: str
    cliente_telefono: str
    direccion_entrega: str
    local_id: int = Field(..., gt=0)
    medio_pago_id: int = Field(..., gt=0)
    notas: Optional[str] = None
    # Puntos a usar (opcional)
    puntos_usar: Optional[int] = Field(default=0, ge=0, description="Puntos a usar para descuento")
    items: List[ItemPedidoCreateBackoffice] = Field(..., min_length=1)


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
    # Información del medio de pago
    medio_pago_id: Optional[int] = None
    medio_pago_codigo: Optional[str] = None
    medio_pago_nombre: Optional[str] = None
    permite_cheque: Optional[bool] = None
    # Información de puntos
    puntos_ganados: Optional[int] = None
    puntos_usados: Optional[int] = None
    descuento_puntos: Optional[float] = None

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
    # Información del medio de pago
    medio_pago_id: Optional[int] = None
    medio_pago_codigo: Optional[str] = None
    medio_pago_nombre: Optional[str] = None
    permite_cheque: Optional[bool] = None
    # Información de puntos
    puntos_ganados: Optional[int] = None
    puntos_usados: Optional[int] = None
    descuento_puntos: Optional[float] = None
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
    # Información del medio de pago
    medio_pago_id: Optional[int] = None
    medio_pago_codigo: Optional[str] = None
    medio_pago_nombre: Optional[str] = None
    permite_cheque: Optional[bool] = None
    # Información de puntos
    puntos_ganados: Optional[int] = None
    puntos_usados: Optional[int] = None
    descuento_puntos: Optional[float] = None
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
    # Información de puntos
    puntos_ganados: Optional[int] = None
    puntos_usados: Optional[int] = None
    descuento_puntos: Optional[float] = None


# Importar para resolver la referencia circular
from .item_pedido import ItemPedidoResponse
from .cliente import ClienteResponse
PedidoConItems.model_rebuild()
PedidoConRelaciones.model_rebuild()
