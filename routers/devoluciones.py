from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from database.models import Devolucion, Pedido, User
from routers.auth import get_current_active_user
from services.devoluciones_service import DevolucionesService, ItemDevolucionInput

router = APIRouter()


class ItemDevolucionSchema(BaseModel):
    item_pedido_id: int
    cantidad_devuelta: float
    local_destino_id: int


class CrearDevolucionSchema(BaseModel):
    motivo: Optional[str] = None
    items: List[ItemDevolucionSchema]


@router.post("/pedidos/{pedido_id}")
def crear_devolucion(
    pedido_id: int,
    body: CrearDevolucionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    items_input = [
        ItemDevolucionInput(
            item_pedido_id=i.item_pedido_id,
            cantidad_devuelta=i.cantidad_devuelta,
            local_destino_id=i.local_destino_id,
        )
        for i in body.items
    ]

    devolucion = DevolucionesService.crear(
        pedido=pedido,
        items_input=items_input,
        motivo=body.motivo,
        usuario_id=current_user.id,
        db=db,
    )
    db.commit()
    db.refresh(devolucion)
    # Recargar con relaciones
    devolucion = (
        db.query(Devolucion)
        .options(joinedload(Devolucion.items))
        .filter(Devolucion.id == devolucion.id)
        .first()
    )
    return devolucion


@router.get("/pedidos/{pedido_id}")
def obtener_devoluciones_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(Devolucion)
        .options(joinedload(Devolucion.items))
        .filter(Devolucion.pedido_id == pedido_id)
        .all()
    )
