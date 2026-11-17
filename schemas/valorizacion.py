"""Schemas de valorización de inventario (change add-valorizacion-inventario)."""
from typing import List, Optional

from pydantic import BaseModel


class ValorizacionItem(BaseModel):
    producto_id: int
    sku: str
    producto_nombre: str
    categoria_id: Optional[int] = None
    categoria_nombre: Optional[str] = None
    local_id: int
    local_nombre: str
    unidad: Optional[str] = None
    stock: float
    costo_unitario: Optional[float] = None
    valor_inventario: Optional[float] = None
    precio_venta_neto: Optional[float] = None
    precio_venta_con_iva: Optional[float] = None  # Precio de lista del local (referencia)
    precio_incluye_iva: bool = True
    valor_venta: Optional[float] = None
    ganancia_potencial: Optional[float] = None
    margen_pct: Optional[float] = None
    sin_costo: bool = False
    sin_precio: bool = False
    stock_negativo: bool = False


class ValorizacionTotales(BaseModel):
    valor_inventario: float = 0
    valor_venta: float = 0
    ganancia_potencial: float = 0
    margen_pct: Optional[float] = None
    productos: int = 0
    sin_costo: int = 0
    sin_precio: int = 0


class ValorizacionResponse(BaseModel):
    items: List[ValorizacionItem]
    totales: ValorizacionTotales
