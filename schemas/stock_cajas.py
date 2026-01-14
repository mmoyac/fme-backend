"""
Esquemas Pydantic para gestión de stock de cajas por proveedor.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StockCajasProveedorBase(BaseModel):
    """Esquema base para stock de cajas por proveedor."""
    producto_id: int = Field(..., description="ID del producto")
    proveedor_id: int = Field(..., description="ID del proveedor")
    cajas_disponibles: int = Field(default=0, description="Cantidad de cajas disponibles en stock")


class StockCajasProveedorCreate(StockCajasProveedorBase):
    """Esquema para crear stock de cajas por proveedor."""
    pass


class StockCajasProveedorUpdate(BaseModel):
    """Esquema para actualizar stock de cajas por proveedor."""
    cajas_disponibles: Optional[int] = Field(None, description="Nueva cantidad de cajas disponibles")


class StockCajasProveedorResponse(StockCajasProveedorBase):
    """Esquema de respuesta para stock de cajas por proveedor."""
    id: int
    cajas_totales_recibidas: int = Field(description="Total histórico de cajas recibidas")
    cajas_totales_vendidas: int = Field(description="Total histórico de cajas vendidas")
    fecha_ultima_actualizacion: datetime
    producto_nombre: Optional[str] = Field(None, description="Nombre del producto")
    producto_sku: Optional[str] = Field(None, description="SKU del producto")
    proveedor_nombre: Optional[str] = Field(None, description="Nombre del proveedor")
    proveedor_rut: Optional[str] = Field(None, description="RUT del proveedor")

    class Config:
        from_attributes = True


class MovimientoStockCajasBase(BaseModel):
    """Esquema base para movimientos de stock de cajas."""
    producto_id: int = Field(..., description="ID del producto")
    proveedor_id: int = Field(..., description="ID del proveedor")
    tipo_movimiento: str = Field(..., description="Tipo de movimiento: ENTRADA_ENROLAMIENTO, SALIDA_PEDIDO, AJUSTE_INVENTARIO")
    cajas_movimiento: int = Field(..., description="Cantidad de cajas movidas (positivo=entrada, negativo=salida)")
    descripcion: Optional[str] = Field(None, description="Descripción del movimiento")


class MovimientoStockCajasCreate(MovimientoStockCajasBase):
    """Esquema para crear movimiento de stock de cajas."""
    lote_id: Optional[int] = Field(None, description="ID del lote origen del movimiento")
    enrolamiento_id: Optional[int] = Field(None, description="ID del enrolamiento origen")
    pedido_id: Optional[int] = Field(None, description="ID del pedido que originó la salida")


class MovimientoStockCajasResponse(MovimientoStockCajasBase):
    """Esquema de respuesta para movimientos de stock de cajas."""
    id: int
    lote_id: Optional[int]
    enrolamiento_id: Optional[int]
    pedido_id: Optional[int]
    cajas_antes: int = Field(description="Stock antes del movimiento")
    cajas_despues: int = Field(description="Stock después del movimiento")
    usuario: str = Field(description="Usuario que realizó el movimiento")
    fecha_movimiento: datetime
    producto_nombre: Optional[str] = Field(None, description="Nombre del producto")
    proveedor_nombre: Optional[str] = Field(None, description="Nombre del proveedor")

    class Config:
        from_attributes = True


class ActualizacionStockCajas(BaseModel):
    """Esquema para actualización de stock por enrolamiento."""
    producto_id: int = Field(..., description="ID del producto")
    proveedor_id: int = Field(..., description="ID del proveedor")
    cajas_a_sumar: int = Field(..., gt=0, description="Cantidad de cajas a agregar al stock")
    lote_id: Optional[int] = Field(None, description="ID del lote del enrolamiento")
    enrolamiento_id: Optional[int] = Field(None, description="ID del enrolamiento")
    descripcion: Optional[str] = Field(None, description="Descripción de la actualización")


class ReservaStockCajas(BaseModel):
    """Esquema para reservar stock de cajas para pedidos."""
    items: list[dict] = Field(..., description="Lista de items a reservar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "producto_id": 1,
                        "proveedor_id": 2,
                        "cajas_requeridas": 3,
                        "peso_por_caja": 1.5
                    }
                ]
            }
        }


class ResumenStockCajas(BaseModel):
    """Esquema para resumen de stock de cajas."""
    total_productos: int = Field(description="Total de productos con stock")
    total_proveedores: int = Field(description="Total de proveedores activos")
    total_cajas_disponibles: int = Field(description="Total de cajas disponibles")
    productos_sin_stock: int = Field(description="Productos sin stock disponible")
    productos_con_stock: list[StockCajasProveedorResponse] = Field(description="Lista de productos con stock")

    class Config:
        from_attributes = True