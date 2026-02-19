"""
Router para endpoints de Precios.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Precio, Producto, Local
from schemas.precio import PrecioResponse, PrecioCreate, PrecioUpdate
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[PrecioResponse])
def listar_precios(
    skip: int = 0,
    limit: int = 100,
    producto_id: int = None,
    local_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista precios del tenant con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de precios
    """
    # Unir con Producto para filtrar por tenant_id
    query = db.query(Precio).join(Producto).filter(Producto.tenant_id == current_user.tenant_id)
    
    if producto_id:
        query = query.filter(Precio.producto_id == producto_id)
    if local_id:
        query = query.filter(Precio.local_id == local_id)
    
    precios = query.offset(skip).limit(limit).all()
    return precios


@router.post("/", response_model=PrecioResponse, status_code=status.HTTP_201_CREATED)
def crear_precio(precio: PrecioCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Crea un nuevo precio para un producto en un local del tenant.
    
    **Validaciones:**
    - Producto y local deben existir y pertenecer al tenant
    - No debe existir otro precio activo para el mismo producto/local
    
    **Uso:** Backoffice - Asignar precio
    """
    # Verificar que producto y local existan y pertenezcan al tenant
    producto = db.query(Producto).filter(Producto.id == precio.producto_id, Producto.tenant_id == current_user.tenant_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {precio.producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == precio.local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {precio.local_id} no encontrado"
        )
    
    # Verificar si ya existe un precio para este producto/local/unidad
    existing = db.query(Precio).filter(
        Precio.producto_id == precio.producto_id,
        Precio.local_id == precio.local_id,
        Precio.unidad_medida_id == precio.unidad_medida_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un precio para este producto/local/unidad. Use PUT para actualizar."
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un precio existente del tenant.
    
    **Uso:** Backoffice - Modificar precio
    """
    # Validar que el precio pertenece al tenant
    db_precio = db.query(Precio).join(Producto).filter(
        Precio.id == precio_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    # Actualizar campos
    if precio.monto_precio is not None:
        db_precio.monto_precio = precio.monto_precio
    if precio.unidad_medida_id is not None:
        db_precio.unidad_medida_id = precio.unidad_medida_id
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.put("/producto/{producto_id}/local/{local_id}/unidad/{unidad_medida_id}", response_model=PrecioResponse)
def actualizar_precio_por_producto_local(
    producto_id: int,
    local_id: int,
    unidad_medida_id: int,
    precio_data: PrecioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza o crea el precio de un producto en un local y unidad específicos del tenant.
    
    **Uso:** Backoffice - Asignar/actualizar precio por producto/local/unidad
    """
    # Verificar que producto y local existan y pertenezcan al tenant
    producto = db.query(Producto).filter(Producto.id == producto_id, Producto.tenant_id == current_user.tenant_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Buscar o crear precio
    db_precio = db.query(Precio).filter(
        Precio.producto_id == producto_id,
        Precio.local_id == local_id,
        Precio.unidad_medida_id == unidad_medida_id
    ).first()
    
    if db_precio:
        # Actualizar existente
        db_precio.monto_precio = precio_data.monto_precio
    else:
        # Crear nuevo
        db_precio = Precio(
            producto_id=producto_id,
            local_id=local_id,
            unidad_medida_id=unidad_medida_id,
            monto_precio=precio_data.monto_precio
        )
        db.add(db_precio)
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.get("/producto/{producto_id}/local/{local_id}", response_model=List[PrecioResponse])
def obtener_precios_producto_local(
    producto_id: int,
    local_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los precios de un producto en un local (por diferentes unidades de medida).
    
    **Uso:** Frontend/Backoffice - Para mostrar opciones de precio por unidad
    """
    precios = db.query(Precio).filter(
        Precio.producto_id == producto_id,
        Precio.local_id == local_id
    ).all()
    
    if not precios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existen precios para producto {producto_id} en local {local_id}"
        )
    
    return precios


@router.delete("/{precio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_precio(precio_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Elimina un precio del tenant.
    
    **Uso:** Backoffice - Eliminar precio
    """
    # Validar que el precio pertenece al tenant
    db_precio = db.query(Precio).join(Producto).filter(
        Precio.id == precio_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    db.delete(db_precio)
    db.commit()
    return None
