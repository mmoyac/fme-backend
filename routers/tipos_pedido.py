"""
Router para gestión de tipos de pedido.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from database.models import TipoPedido, Local
from schemas.tipo_pedido import (
    TipoPedidoResponse, 
    TipoPedidoCreate, 
    TipoPedidoUpdate
)
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[TipoPedidoResponse])
def listar_tipos_pedido(
    skip: int = 0,
    limit: int = 5000,
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos los tipos de pedido.
    
    **Uso:** Obtener tipos disponibles para seleccionar en formularios
    """
    query = db.query(TipoPedido).options(
        joinedload(TipoPedido.local_despacho_default)
    )
    
    if activo is not None:
        query = query.filter(TipoPedido.activo == activo)
    
    tipos = query.order_by(TipoPedido.id).offset(skip).limit(limit).all()
    return tipos


@router.get("/{tipo_id}", response_model=TipoPedidoResponse)
def obtener_tipo_pedido(
    tipo_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene un tipo de pedido por ID.
    """
    tipo = db.query(TipoPedido).options(
        joinedload(TipoPedido.local_despacho_default)
    ).filter(TipoPedido.id == tipo_id).first()
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de pedido con ID {tipo_id} no encontrado"
        )
    return tipo


@router.get("/codigo/{codigo}", response_model=TipoPedidoResponse)
def obtener_tipo_pedido_por_codigo(
    codigo: str, 
    db: Session = Depends(get_db)
):
    """
    Obtiene un tipo de pedido por código.
    
    **Uso:** Buscar tipo por código (ej: 'PRODUCTOS', 'CAJAS_VARIABLES')
    """
    tipo = db.query(TipoPedido).options(
        joinedload(TipoPedido.local_despacho_default)
    ).filter(TipoPedido.codigo == codigo).first()
    
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de pedido con código '{codigo}' no encontrado"
        )
    return tipo


@router.post("/", response_model=TipoPedidoResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo_pedido(
    tipo_data: TipoPedidoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Crea un nuevo tipo de pedido.
    
    **Uso:** Backoffice - Admin puede crear nuevos tipos
    """
    # Verificar que el código no exista
    tipo_existente = db.query(TipoPedido).filter(TipoPedido.codigo == tipo_data.codigo).first()
    if tipo_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un tipo de pedido con código '{tipo_data.codigo}'"
        )
    
    # Verificar que el local exista si se proporciona
    if tipo_data.local_despacho_default_id:
        local = db.query(Local).filter(Local.id == tipo_data.local_despacho_default_id).first()
        if not local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El local especificado no existe"
            )
    
    db_tipo = TipoPedido(**tipo_data.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    
    # Recargar con relaciones
    tipo_with_relations = db.query(TipoPedido).options(
        joinedload(TipoPedido.local_despacho_default)
    ).filter(TipoPedido.id == db_tipo.id).first()
    
    return tipo_with_relations


@router.put("/{tipo_id}", response_model=TipoPedidoResponse)
def actualizar_tipo_pedido(
    tipo_id: int,
    tipo_data: TipoPedidoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un tipo de pedido existente.
    """
    tipo = db.query(TipoPedido).filter(TipoPedido.id == tipo_id).first()
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de pedido con ID {tipo_id} no encontrado"
        )
    
    # Si se actualiza el código, verificar que no exista
    if tipo_data.codigo and tipo_data.codigo != tipo.codigo:
        tipo_existente = db.query(TipoPedido).filter(TipoPedido.codigo == tipo_data.codigo).first()
        if tipo_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un tipo de pedido con código '{tipo_data.codigo}'"
            )
    
    # Verificar que el local exista si se proporciona
    if tipo_data.local_despacho_default_id:
        local = db.query(Local).filter(Local.id == tipo_data.local_despacho_default_id).first()
        if not local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El local especificado no existe"
            )
    
    update_data = tipo_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tipo, field, value)
    
    db.commit()
    db.refresh(tipo)
    
    # Recargar con relaciones
    tipo_with_relations = db.query(TipoPedido).options(
        joinedload(TipoPedido.local_despacho_default)
    ).filter(TipoPedido.id == tipo.id).first()
    
    return tipo_with_relations