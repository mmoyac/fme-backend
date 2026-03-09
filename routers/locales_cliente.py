"""
Router para endpoints de LocalCliente (locales propios de un cliente).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import LocalCliente, Cliente
from schemas.local_cliente import LocalClienteCreate, LocalClienteUpdate, LocalClienteResponse
from routers.auth import get_current_active_user

router = APIRouter(prefix="/api/locales_cliente", tags=["LocalesCliente"])

@router.get("/cliente/{cliente_id}", response_model=List[LocalClienteResponse])
def listar_locales_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los locales propios de un cliente.
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.tenant_id == current_user.tenant_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db.query(LocalCliente).filter(LocalCliente.cliente_id == cliente_id).all()

@router.get("/{local_cliente_id}", response_model=LocalClienteResponse)
def obtener_local_cliente(
    local_cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    local_cliente = db.query(LocalCliente).join(Cliente).filter(
        LocalCliente.id == local_cliente_id,
        Cliente.tenant_id == current_user.tenant_id
    ).first()
    if not local_cliente:
        raise HTTPException(status_code=404, detail="Local de cliente no encontrado")
    return local_cliente

@router.post("/", response_model=LocalClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_local_cliente(
    local_cliente: LocalClienteCreate,
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.tenant_id == current_user.tenant_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    nuevo_local = LocalCliente(**local_cliente.dict(), cliente_id=cliente_id)
    db.add(nuevo_local)
    db.commit()
    db.refresh(nuevo_local)
    return nuevo_local

@router.put("/{local_cliente_id}", response_model=LocalClienteResponse)
def actualizar_local_cliente(
    local_cliente_id: int,
    local_cliente_update: LocalClienteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    local_cliente = db.query(LocalCliente).join(Cliente).filter(
        LocalCliente.id == local_cliente_id,
        Cliente.tenant_id == current_user.tenant_id
    ).first()
    if not local_cliente:
        raise HTTPException(status_code=404, detail="Local de cliente no encontrado")
    for field, value in local_cliente_update.dict(exclude_unset=True).items():
        setattr(local_cliente, field, value)
    db.commit()
    db.refresh(local_cliente)
    return local_cliente

@router.delete("/{local_cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_local_cliente(
    local_cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    local_cliente = db.query(LocalCliente).join(Cliente).filter(
        LocalCliente.id == local_cliente_id,
        Cliente.tenant_id == current_user.tenant_id
    ).first()
    if not local_cliente:
        raise HTTPException(status_code=404, detail="Local de cliente no encontrado")
    db.delete(local_cliente)
    db.commit()
    return None
