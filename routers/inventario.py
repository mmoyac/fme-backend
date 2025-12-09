"""
Router para endpoints de Inventario.
Consultas de disponibilidad y stock.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Inventario, Producto, Local
from schemas.inventario_consulta import InventarioResumen, InventarioDetalle
from schemas.inventario import InventarioResponse, InventarioUpdate
from services import inventario_service

router = APIRouter()


@router.get("/resumen", response_model=List[InventarioResumen])
def obtener_resumen_inventario(db: Session = Depends(get_db)):
    """
    Obtiene el resumen de inventario de todos los productos.
    
    Retorna una lista con:
    - SKU del producto
    - Nombre del producto
    - Stock total (suma de todos los locales)
    
    **Ideal para:** Listar productos disponibles en un chat o interfaz
    """
    resumen = inventario_service.get_resumen_inventario(db)
    return resumen


@router.get("/detalle/{sku}", response_model=InventarioDetalle)
def obtener_detalle_inventario(
    sku: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el detalle de inventario de un producto específico por SKU.
    
    Retorna:
    - Información del producto (SKU, nombre, descripción)
    - Stock total
    - Detalle de stock por cada local (nombre, dirección, cantidad)
    
    **Ideal para:** Mostrar disponibilidad por sucursal cuando el usuario pregunta por un producto
    
    - **sku**: Código SKU del producto a consultar
    """
    detalle = inventario_service.get_detalle_inventario_by_sku(db, sku)
    
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con SKU '{sku}' no encontrado"
        )
    
    return detalle


# --------------------------------------------------
# CRUD Endpoints para Backoffice
# --------------------------------------------------

@router.get("/", response_model=List[InventarioResponse])
def listar_inventario(
    skip: int = 0,
    limit: int = 100,
    producto_id: int = None,
    local_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Lista registros de inventario con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de inventario
    """
    query = db.query(Inventario)
    
    if producto_id:
        query = query.filter(Inventario.producto_id == producto_id)
    if local_id:
        query = query.filter(Inventario.local_id == local_id)
    
    inventarios = query.offset(skip).limit(limit).all()
    return inventarios


@router.put("/{inventario_id}", response_model=InventarioResponse)
def actualizar_inventario(
    inventario_id: int,
    inventario: InventarioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el stock de un registro de inventario.
    
    **Uso:** Backoffice - Ajustar stock
    """
    db_inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not db_inventario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventario con ID {inventario_id} no encontrado"
        )
    
    # Actualizar stock
    if inventario.cantidad_stock is not None:
        db_inventario.cantidad_stock = inventario.cantidad_stock
    
    db.commit()
    db.refresh(db_inventario)
    return db_inventario


@router.put("/producto/{producto_id}/local/{local_id}", response_model=InventarioResponse)
def actualizar_inventario_por_producto_local(
    producto_id: int,
    local_id: int,
    inventario_data: InventarioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza o crea el stock de un producto en un local específico.
    
    **Uso:** Backoffice - Ajustar stock por producto/local
    """
    # Verificar que producto y local existan
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == local_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Buscar o crear inventario
    db_inventario = db.query(Inventario).filter(
        Inventario.producto_id == producto_id,
        Inventario.local_id == local_id
    ).first()
    
    if db_inventario:
        # Actualizar existente
        db_inventario.cantidad_stock = inventario_data.cantidad_stock
    else:
        # Crear nuevo
        db_inventario = Inventario(
            producto_id=producto_id,
            local_id=local_id,
            cantidad_stock=inventario_data.cantidad_stock
        )
        db.add(db_inventario)
    
    db.commit()
    db.refresh(db_inventario)
    return db_inventario
