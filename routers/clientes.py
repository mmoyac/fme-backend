"""
Router para endpoints de Clientes.
CRUD completo para gestión de clientes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Cliente, Pedido
from schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from services.puntos_service import PuntosService
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los clientes del tenant con paginación e información de puntos.
    
    **Uso:** Backoffice - Tabla de clientes
    """
    clientes = db.query(Cliente).filter(Cliente.tenant_id == current_user.tenant_id).offset(skip).limit(limit).all()
    
    # Enriquecer con información de puntos
    clientes_con_puntos = []
    for cliente in clientes:
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        
        cliente_data = {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "comuna": cliente.comuna,
            "limite_credito": float(cliente.limite_credito),
            "credito_usado": float(cliente.credito_usado),
            "puntos_disponibles": puntos_cliente.puntos_disponibles,
            "puntos_totales_ganados": puntos_cliente.puntos_totales_ganados,
            "puntos_totales_usados": puntos_cliente.puntos_totales_usados
        }
        clientes_con_puntos.append(cliente_data)
    
    return clientes_con_puntos


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtiene un cliente específico por ID con información completa de puntos.
    
    **Uso:** Backoffice - Ver detalle de cliente
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.tenant_id == current_user.tenant_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Obtener información de puntos
    puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
    
    return {
        "id": cliente.id,
        "nombre": cliente.nombre,
        "apellido": cliente.apellido,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "direccion": cliente.direccion,
        "comuna": cliente.comuna,
        "limite_credito": float(cliente.limite_credito),
        "credito_usado": float(cliente.credito_usado),
        "puntos_disponibles": puntos_cliente.puntos_disponibles,
        "puntos_totales_ganados": puntos_cliente.puntos_totales_ganados,
        "puntos_totales_usados": puntos_cliente.puntos_totales_usados
    }


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Crea un nuevo cliente con información inicial de puntos.
    
    **Uso:** Backoffice - Alta de cliente
    """
    # Normalizar email vacío a None
    email_normalizado = cliente.email.strip() if cliente.email else None
    if email_normalizado == "":
        email_normalizado = None
        
    # Verificar si el email ya existe (si se proporciona) dentro del tenant
    if email_normalizado:
        cliente_existente = db.query(Cliente).filter(Cliente.email == email_normalizado, Cliente.tenant_id == current_user.tenant_id).first()
        if cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un cliente con el email '{email_normalizado}'"
            )
    
    # Crear cliente con email normalizado y tenant_id
    cliente_data = cliente.model_dump()
    cliente_data['email'] = email_normalizado
    cliente_data['tenant_id'] = current_user.tenant_id
    db_cliente = Cliente(**cliente_data)
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    
    # Crear registro inicial de puntos
    puntos_cliente = PuntosService.obtener_puntos_cliente(db, db_cliente.id)
    
    return {
        "id": db_cliente.id,
        "nombre": db_cliente.nombre,
        "apellido": db_cliente.apellido,
        "email": db_cliente.email,
        "telefono": db_cliente.telefono,
        "direccion": db_cliente.direccion,
        "comuna": db_cliente.comuna,
        "limite_credito": float(db_cliente.limite_credito),
        "credito_usado": float(db_cliente.credito_usado),
        "puntos_disponibles": puntos_cliente.puntos_disponibles,
        "puntos_totales_ganados": puntos_cliente.puntos_totales_ganados,
        "puntos_totales_usados": puntos_cliente.puntos_totales_usados
    }


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    cliente: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza los datos de un cliente y retorna información completa incluyendo puntos.
    
    **Uso:** Backoffice - Editar cliente
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.tenant_id == current_user.tenant_id).first()
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar email único si se está actualizando dentro del tenant
    email_normalizado = None
    if cliente.email is not None:
        email_normalizado = cliente.email.strip()
        if email_normalizado == "":
            email_normalizado = None
            
        if email_normalizado and email_normalizado != db_cliente.email:
            cliente_existente = db.query(Cliente).filter(Cliente.email == email_normalizado, Cliente.tenant_id == current_user.tenant_id).first()
            if cliente_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un cliente con el email '{email_normalizado}'"
                )
    
    # Actualizar campos
    update_data = cliente.model_dump(exclude_unset=True)
    if 'email' in update_data:
        update_data['email'] = email_normalizado
    for field, value in update_data.items():
        setattr(db_cliente, field, value)
    
    db.commit()
    db.refresh(db_cliente)
    
    # Obtener información de puntos actualizada
    puntos_cliente = PuntosService.obtener_puntos_cliente(db, db_cliente.id)
    
    return {
        "id": db_cliente.id,
        "nombre": db_cliente.nombre,
        "apellido": db_cliente.apellido,
        "email": db_cliente.email,
        "telefono": db_cliente.telefono,
        "direccion": db_cliente.direccion,
        "comuna": db_cliente.comuna,
        "limite_credito": float(db_cliente.limite_credito),
        "credito_usado": float(db_cliente.credito_usado),
        "puntos_disponibles": puntos_cliente.puntos_disponibles,
        "puntos_totales_ganados": puntos_cliente.puntos_totales_ganados,
        "puntos_totales_usados": puntos_cliente.puntos_totales_usados
    }


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(
    cliente_id: int,
    force: bool = False,  # Parámetro para forzar eliminación
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Elimina un cliente del tenant.
    
    **Uso:** Backoffice - Borrar cliente
    **Nota:** Por defecto, no se puede eliminar si tiene pedidos asociados.
    Use force=true para eliminar de todos modos (útil para resets completos).
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.tenant_id == current_user.tenant_id).first()
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    # Verificar si tiene pedidos (solo si no se está forzando)
    if not force:
        pedidos_count = db.query(Pedido).filter(Pedido.cliente_id == cliente_id).count()
        if pedidos_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el cliente porque tiene {pedidos_count} pedido(s) asociado(s). Use force=true para eliminar de todos modos."
            )
    
    db.delete(db_cliente)
    db.commit()
    return None
