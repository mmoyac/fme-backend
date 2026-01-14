from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date
from .maestras import TipoProveedor

# --- Proveedores ---

class ProveedorBase(BaseModel):
    nombre: str
    rut: Optional[str] = None
    contacto: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_proveedor_id: Optional[int] = None
    activo: bool = True

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    rut: Optional[str] = None
    contacto: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_proveedor_id: Optional[int] = None
    activo: Optional[bool] = None

class ProveedorRead(ProveedorBase):
    id: int
    tipo_proveedor: Optional[TipoProveedor] = None

    class Config:
        from_attributes = True

# --- Compras ---

class DetalleCompraBase(BaseModel):
    producto_id: int
    cantidad: float
    precio_unitario: float

class DetalleCompraCreate(DetalleCompraBase):
    pass

class DetalleCompraRead(DetalleCompraBase):
    id: int
    producto_nombre: Optional[str] = None # Helper

    class Config:
        orm_mode = True

class CompraBase(BaseModel):
    proveedor_id: int
    local_id: int
    tipo_documento_id: int
    fecha_compra: Optional[Union[datetime, date]] = None
    numero_documento: Optional[str] = None
    notas: Optional[str] = None

class CompraCreate(CompraBase):
    detalles: List[DetalleCompraCreate]

class CompraRead(CompraBase):
    id: int
    monto_total: float
    estado: str
    detalles: List[DetalleCompraRead] = []

    class Config:
        orm_mode = True
