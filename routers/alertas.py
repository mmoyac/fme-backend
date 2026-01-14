"""
Router para alertas y notificaciones del sistema.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from database.database import get_db
from database.models import (
    User, 
    Producto as ProductoModel,
    Proveedor as ProveedorModel, 
    PrecioProveedor as PrecioProveedorModel,
    Enrolamiento as EnrolamientoModel,
    Lote as LoteModel,
    EstadoEnrolamiento as EstadoEnrolamientoModel
)
from routers.auth import get_current_active_user
from pydantic import BaseModel

router = APIRouter()


class EnrolamientoPendiente(BaseModel):
    enrolamiento_id: int
    patente: str
    estado: str
    cajas_producto: int
    peso_kg: float
    
    class Config:
        from_attributes = True


class ProductoSinPrecio(BaseModel):
    producto_id: int
    producto_nombre: str
    producto_sku: str
    proveedor_id: int
    proveedor_nombre: str
    enrolamientos_pendientes: List[EnrolamientoPendiente]
    total_cajas: int
    peso_total_kg: float
    
    class Config:
        from_attributes = True


@router.get("/productos-sin-precio", response_model=List[ProductoSinPrecio])
def obtener_productos_sin_precio(
    db: Session = Depends(get_db)
):
    """
    Obtener productos que existen en enrolamientos activos 
    pero no tienen precio configurado para el proveedor correspondiente.
    """
    # Subconsulta para obtener combinaciones proveedor-producto con precios configurados
    productos_con_precio = (
        db.query(
            PrecioProveedorModel.proveedor_id,
            PrecioProveedorModel.producto_id
        )
        .distinct()
        .subquery()
    )
    
    # Consulta principal: obtener lotes de enrolamientos activos
    # donde NO existe precio configurado para esa combinación proveedor-producto
    resultados = (
        db.query(
            LoteModel.producto_id,
            ProductoModel.nombre.label('producto_nombre'),
            ProductoModel.sku.label('producto_sku'),
            EnrolamientoModel.proveedor_id,
            ProveedorModel.nombre.label('proveedor_nombre'),
            EnrolamientoModel.id.label('enrolamiento_id'),
            EnrolamientoModel.patente,
            EstadoEnrolamientoModel.nombre.label('estado_nombre'),
            func.count(LoteModel.id).label('cajas_producto'),
            func.sum(LoteModel.peso_actual).label('peso_kg')
        )
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .join(EnrolamientoModel, LoteModel.enrolamiento_id == EnrolamientoModel.id)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .join(EstadoEnrolamientoModel, EnrolamientoModel.estado_id == EstadoEnrolamientoModel.id)
        .outerjoin(
            productos_con_precio,
            and_(
                productos_con_precio.c.proveedor_id == EnrolamientoModel.proveedor_id,
                productos_con_precio.c.producto_id == LoteModel.producto_id
            )
        )
        .filter(productos_con_precio.c.proveedor_id.is_(None))  # NO tiene precio configurado
        .filter(EstadoEnrolamientoModel.codigo.in_(['PENDIENTE', 'EN_PROCESO', 'FINALIZADO']))  # Enrolamientos activos
        .group_by(
            LoteModel.producto_id,
            ProductoModel.nombre,
            ProductoModel.sku,
            EnrolamientoModel.proveedor_id,
            ProveedorModel.nombre,
            EnrolamientoModel.id,
            EnrolamientoModel.patente,
            EstadoEnrolamientoModel.nombre
        )
        .all()
    )
    
    # Agrupar por producto-proveedor
    productos_agrupados = {}
    
    for resultado in resultados:
        clave = f"{resultado.producto_id}_{resultado.proveedor_id}"
        
        enrolamiento_info = EnrolamientoPendiente(
            enrolamiento_id=resultado.enrolamiento_id,
            patente=resultado.patente,
            estado=resultado.estado_nombre,
            cajas_producto=resultado.cajas_producto,
            peso_kg=float(resultado.peso_kg) if resultado.peso_kg else 0.0
        )
        
        if clave not in productos_agrupados:
            productos_agrupados[clave] = ProductoSinPrecio(
                producto_id=resultado.producto_id,
                producto_nombre=resultado.producto_nombre,
                producto_sku=resultado.producto_sku,
                proveedor_id=resultado.proveedor_id,
                proveedor_nombre=resultado.proveedor_nombre,
                enrolamientos_pendientes=[enrolamiento_info],
                total_cajas=resultado.cajas_producto,
                peso_total_kg=float(resultado.peso_kg) if resultado.peso_kg else 0.0
            )
        else:
            productos_agrupados[clave].enrolamientos_pendientes.append(enrolamiento_info)
            productos_agrupados[clave].total_cajas += resultado.cajas_producto
            productos_agrupados[clave].peso_total_kg += float(resultado.peso_kg) if resultado.peso_kg else 0.0
    
    return list(productos_agrupados.values())