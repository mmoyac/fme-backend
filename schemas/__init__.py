"""
Módulo de schemas Pydantic.
"""
from .producto import ProductoBase, ProductoCreate, ProductoUpdate, ProductoResponse
from .local import LocalBase, LocalCreate, LocalUpdate, LocalResponse
from .cliente import ClienteBase, ClienteCreate, ClienteUpdate, ClienteResponse
from .inventario import InventarioBase, InventarioCreate, InventarioUpdate, InventarioResponse
from .precio import PrecioBase, PrecioCreate, PrecioUpdate, PrecioResponse
from .pedido import PedidoBase, PedidoCreate, PedidoUpdate, PedidoResponse, PedidoConItems, EstadoPedido
from .item_pedido import ItemPedidoBase, ItemPedidoCreate, ItemPedidoUpdate, ItemPedidoResponse

__all__ = [
    # Producto
    "ProductoBase", "ProductoCreate", "ProductoUpdate", "ProductoResponse",
    # Local
    "LocalBase", "LocalCreate", "LocalUpdate", "LocalResponse",
    # Cliente
    "ClienteBase", "ClienteCreate", "ClienteUpdate", "ClienteResponse",
    # Inventario
    "InventarioBase", "InventarioCreate", "InventarioUpdate", "InventarioResponse",
    # Precio
    "PrecioBase", "PrecioCreate", "PrecioUpdate", "PrecioResponse",
    # Pedido
    "PedidoBase", "PedidoCreate", "PedidoUpdate", "PedidoResponse", "PedidoConItems", "EstadoPedido",
    # ItemPedido
    "ItemPedidoBase", "ItemPedidoCreate", "ItemPedidoUpdate", "ItemPedidoResponse",
]
