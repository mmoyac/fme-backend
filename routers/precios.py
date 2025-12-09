"""
Router para endpoints de Precios.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Precio, Producto, Local
from schemas.precio import PrecioResponse, PrecioCreate, PrecioUpdate

router = APIRouter()


@router.get("/", response_model=List[PrecioResponse])
def listar_precios(
    skip: int = 0,
    limit: int = 100,
    producto_id: int = None,
    local_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Lista precios con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de precios
    """
    query = db.query(Precio)
    
    if producto_id:
        query = query.filter(Precio.producto_id == producto_id)
    if local_id:
        query = query.filter(Precio.local_id == local_id)
    
    precios = query.offset(skip).limit(limit).all()
    return precios


@router.post("/", response_model=PrecioResponse, status_code=status.HTTP_201_CREATED)
def crear_precio(precio: PrecioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo precio para un producto en un local.
    
    **Validaciones:**
    - Producto y local deben existir
    - No debe existir otro precio activo para el mismo producto/local
    
    **Uso:** Backoffice - Asignar precio
    """
    # Verificar que producto y local existan
    producto = db.query(Producto).filter(Producto.id == precio.producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {precio.producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == precio.local_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {precio.local_id} no encontrado"
        )
    
    # Verificar si ya existe un precio para este producto/local
    existing = db.query(Precio).filter(
        Precio.producto_id == precio.producto_id,
        Precio.local_id == precio.local_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un precio para este producto en este local. Use PUT para actualizar."
        )
    
    # Crear nuevo precio
    db_precio = Precio(**precio.model_dump())
    db.add(db_precio)
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.put("/{precio_id}", response_model=PrecioResponse)
def actualizar_precio(
    precio_id: int,
    precio: PrecioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un precio existente.
    
    **Uso:** Backoffice - Modificar precio
    """
    db_precio = db.query(Precio).filter(Precio.id == precio_id).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    # Actualizar monto
    if precio.monto_precio is not None:
        db_precio.monto_precio = precio.monto_precio
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.put("/producto/{producto_id}/local/{local_id}", response_model=PrecioResponse)
def actualizar_precio_por_producto_local(
    producto_id: int,
    local_id: int,
    precio_data: PrecioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza o crea el precio de un producto en un local específico.
    
    **Uso:** Backoffice - Asignar/actualizar precio por producto/local
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
    
    # Buscar o crear precio
    db_precio = db.query(Precio).filter(
        Precio.producto_id == producto_id,
        Precio.local_id == local_id
    ).first()
    
    if db_precio:
        # Actualizar existente
        db_precio.monto_precio = precio_data.monto_precio
    else:
        # Crear nuevo
        db_precio = Precio(
            producto_id=producto_id,
            local_id=local_id,
            monto_precio=precio_data.monto_precio
        )
        db.add(db_precio)
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.delete("/{precio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_precio(precio_id: int, db: Session = Depends(get_db)):
    """
    Elimina un precio.
    
    **Uso:** Backoffice - Eliminar precio
    """
    db_precio = db.query(Precio).filter(Precio.id == precio_id).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    db.delete(db_precio)
    db.commit()
    return None
