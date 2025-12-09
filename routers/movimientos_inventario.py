"""
Router para endpoints de Movimientos de Inventario.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database.database import get_db
from database.models import MovimientoInventario, Inventario, Producto, Local
from schemas.movimiento_inventario import (
    TransferenciaInventario,
    AjusteInventario,
    MovimientoInventarioResponse
)

router = APIRouter()


@router.post("/transferencia", response_model=dict, status_code=status.HTTP_201_CREATED)
def transferir_inventario(
    transferencia: TransferenciaInventario,
    db: Session = Depends(get_db)
):
    """
    Transfiere inventario de un local a otro.
    
    **Validaciones:**
    - Stock suficiente en local origen
    - Producto y locales existen
    - Crea entrada en movimientos
    - Actualiza inventarios
    """
    # Validar que los locales sean diferentes
    if transferencia.local_origen_id == transferencia.local_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El local de origen y destino deben ser diferentes"
        )
    
    # Validar producto existe
    producto = db.query(Producto).filter(Producto.id == transferencia.producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {transferencia.producto_id} no encontrado"
        )
    
    # Validar locales existen
    local_origen = db.query(Local).filter(Local.id == transferencia.local_origen_id).first()
    local_destino = db.query(Local).filter(Local.id == transferencia.local_destino_id).first()
    
    if not local_origen or not local_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local de origen o destino no encontrado"
        )
    
    # Obtener inventario origen
    inv_origen = db.query(Inventario).filter(
        Inventario.producto_id == transferencia.producto_id,
        Inventario.local_id == transferencia.local_origen_id
    ).first()
    
    if not inv_origen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El producto no tiene inventario en {local_origen.nombre}"
        )
    
    if inv_origen.cantidad_stock < transferencia.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente en {local_origen.nombre}. Disponible: {inv_origen.cantidad_stock}"
        )
    
    # Obtener o crear inventario destino
    inv_destino = db.query(Inventario).filter(
        Inventario.producto_id == transferencia.producto_id,
        Inventario.local_id == transferencia.local_destino_id
    ).first()
    
    if not inv_destino:
        inv_destino = Inventario(
            producto_id=transferencia.producto_id,
            local_id=transferencia.local_destino_id,
            cantidad_stock=0
        )
        db.add(inv_destino)
        db.flush()
    
    # Realizar transferencia
    inv_origen.cantidad_stock -= transferencia.cantidad
    inv_destino.cantidad_stock += transferencia.cantidad
    
    # Registrar movimiento
    movimiento = MovimientoInventario(
        producto_id=transferencia.producto_id,
        local_origen_id=transferencia.local_origen_id,
        local_destino_id=transferencia.local_destino_id,
        cantidad=transferencia.cantidad,
        tipo_movimiento="TRANSFERENCIA",
        notas=transferencia.notas,
        usuario="admin"
    )
    db.add(movimiento)
    
    db.commit()
    db.refresh(movimiento)
    
    return {
        "mensaje": f"Transferencia exitosa: {transferencia.cantidad} unidades de {producto.nombre}",
        "origen": {
            "local": local_origen.nombre,
            "stock_anterior": inv_origen.cantidad_stock + transferencia.cantidad,
            "stock_nuevo": inv_origen.cantidad_stock
        },
        "destino": {
            "local": local_destino.nombre,
            "stock_anterior": inv_destino.cantidad_stock - transferencia.cantidad,
            "stock_nuevo": inv_destino.cantidad_stock
        },
        "movimiento_id": movimiento.id
    }


@router.get("/historial", response_model=List[MovimientoInventarioResponse])
def listar_movimientos(
    skip: int = 0,
    limit: int = 100,
    producto_id: Optional[int] = None,
    local_id: Optional[int] = None,
    tipo_movimiento: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista el historial de movimientos de inventario.
    
    **Filtros opcionales:**
    - producto_id: Movimientos de un producto específico
    - local_id: Movimientos que involucran un local (origen o destino)
    - tipo_movimiento: TRANSFERENCIA, AJUSTE, PEDIDO, etc.
    """
    query = db.query(MovimientoInventario)
    
    if producto_id:
        query = query.filter(MovimientoInventario.producto_id == producto_id)
    
    if local_id:
        query = query.filter(
            (MovimientoInventario.local_origen_id == local_id) |
            (MovimientoInventario.local_destino_id == local_id)
        )
    
    if tipo_movimiento:
        query = query.filter(MovimientoInventario.tipo_movimiento == tipo_movimiento)
    
    movimientos = query.order_by(
        MovimientoInventario.fecha_movimiento.desc()
    ).offset(skip).limit(limit).all()
    
    # Mapear con información de relaciones
    result = []
    for mov in movimientos:
        mov_dict = {
            'id': mov.id,
            'producto_id': mov.producto_id,
            'local_origen_id': mov.local_origen_id,
            'local_destino_id': mov.local_destino_id,
            'cantidad': mov.cantidad,
            'tipo_movimiento': mov.tipo_movimiento,
            'referencia_id': mov.referencia_id,
            'notas': mov.notas,
            'usuario': mov.usuario,
            'fecha_movimiento': mov.fecha_movimiento,
            'producto': {
                'id': mov.producto.id,
                'nombre': mov.producto.nombre,
                'sku': mov.producto.sku
            } if mov.producto else None,
            'local_origen': {
                'id': mov.local_origen.id,
                'nombre': mov.local_origen.nombre
            } if mov.local_origen else None,
            'local_destino': {
                'id': mov.local_destino.id,
                'nombre': mov.local_destino.nombre
            } if mov.local_destino else None
        }
        result.append(mov_dict)
    
    return result
