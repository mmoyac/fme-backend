"""
Router para endpoints de Clientes.
CRUD completo para gestión de clientes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Cliente
from schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter()


@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista todos los clientes con paginación.
    
    **Uso:** Backoffice - Tabla de clientes
    """
    clientes = db.query(Cliente).offset(skip).limit(limit).all()
    return clientes


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene un cliente específico por ID.
    
    **Uso:** Backoffice - Ver detalle de cliente
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    return cliente


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo cliente.
    
    **Uso:** Backoffice - Alta de cliente
    """
    # Verificar si el email ya existe (si se proporciona)
    if cliente.email:
        cliente_existente = db.query(Cliente).filter(Cliente.email == cliente.email).first()
        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el email '{cliente.email}'"
            )
    
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    cliente: ClienteUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un cliente.
    
    **Uso:** Backoffice - Editar cliente
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar email único si se está actualizando
    if cliente.email and cliente.email != db_cliente.email:
        cliente_existente = db.query(Cliente).filter(Cliente.email == cliente.email).first()
        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el email '{cliente.email}'"
            )
    
    # Actualizar campos
    update_data = cliente.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cliente, field, value)
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un cliente.
    
    **Uso:** Backoffice - Borrar cliente
    **Nota:** No se puede eliminar si tiene pedidos asociados.
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar si tiene pedidos
    if db_cliente.pedidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar el cliente porque tiene {len(db_cliente.pedidos)} pedido(s) asociado(s)"
        )
    
    db.delete(db_cliente)
    db.commit()
    return None
