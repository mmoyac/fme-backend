from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import date
from pydantic import BaseModel

from database.database import get_db
from database.models import NotaCredito, Devolucion, ItemDevolucion, User
from routers.auth import get_current_active_user
from services.notas_credito_service import NotasCreditoService


def _serializar_nota(nota: NotaCredito) -> dict:
    items_devolucion = []
    if nota.devolucion and nota.devolucion.items:
        for item in nota.devolucion.items:
            items_devolucion.append({
                "producto": item.producto.nombre if item.producto else f"ID {item.producto_id}",
                "cantidad_devuelta": float(item.cantidad_devuelta),
                "local_destino": item.local_destino.nombre if item.local_destino else None,
            })

    return {
        "id": nota.id,
        "tenant_id": nota.tenant_id,
        "pedido_id": nota.pedido_id,
        "tipo_documento_id": nota.tipo_documento_id,
        "monto": float(nota.monto),
        "motivo": nota.motivo,
        "folio_sii": nota.folio_sii,
        "fecha_emision": nota.fecha_emision.isoformat() if nota.fecha_emision else None,
        "estado_sii": nota.estado_sii,
        "pedido": {"numero_pedido": nota.pedido.numero_pedido} if nota.pedido else None,
        "tipo_documento": {
            "id": nota.tipo_documento.id,
            "codigo": nota.tipo_documento.codigo,
            "nombre": nota.tipo_documento.nombre,
        } if nota.tipo_documento else None,
        "items_devolucion": items_devolucion,
    }

router = APIRouter()


class ActualizarNotaCreditoRequest(BaseModel):
    folio_sii: Optional[str] = None
    estado_sii: Optional[str] = None


@router.get("/")
def listar_notas_credito(
    tenant_id: Optional[int] = Query(None),
    tipo_documento_id: Optional[int] = Query(None),
    estado_sii: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(NotaCredito)

    if tenant_id:
        query = query.filter(NotaCredito.tenant_id == tenant_id)
    if tipo_documento_id:
        query = query.filter(NotaCredito.tipo_documento_id == tipo_documento_id)
    if estado_sii:
        query = query.filter(NotaCredito.estado_sii == estado_sii)
    if fecha_desde:
        query = query.filter(NotaCredito.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.filter(NotaCredito.fecha_emision <= fecha_hasta)

    total = query.count()
    notas = (
        query
        .options(
            joinedload(NotaCredito.tipo_documento),
            joinedload(NotaCredito.pedido),
            joinedload(NotaCredito.devolucion).joinedload(Devolucion.items).joinedload(ItemDevolucion.producto),
            joinedload(NotaCredito.devolucion).joinedload(Devolucion.items).joinedload(ItemDevolucion.local_destino),
        )
        .order_by(desc(NotaCredito.fecha_emision))
        .offset(skip).limit(limit).all()
    )

    return {"total": total, "items": [_serializar_nota(n) for n in notas]}


@router.get("/{nota_id}")
def obtener_nota_credito(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    nota = db.query(NotaCredito).filter(NotaCredito.id == nota_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota de crédito no encontrada")
    return nota


@router.patch("/{nota_id}")
def actualizar_nota_credito(
    nota_id: int,
    body: ActualizarNotaCreditoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    nota = db.query(NotaCredito).filter(NotaCredito.id == nota_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota de crédito no encontrada")
    if body.folio_sii is not None:
        nota.folio_sii = body.folio_sii or None
    if body.estado_sii is not None:
        nota.estado_sii = body.estado_sii
    db.commit()
    db.refresh(nota)
    # Recargar con relaciones
    nota = (
        db.query(NotaCredito)
        .options(
            joinedload(NotaCredito.tipo_documento),
            joinedload(NotaCredito.pedido),
            joinedload(NotaCredito.devolucion).joinedload(Devolucion.items).joinedload(ItemDevolucion.producto),
            joinedload(NotaCredito.devolucion).joinedload(Devolucion.items).joinedload(ItemDevolucion.local_destino),
        )
        .filter(NotaCredito.id == nota_id)
        .first()
    )
    return _serializar_nota(nota)


@router.get("/pedido/{pedido_id}")
def obtener_nota_credito_por_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    nota = NotasCreditoService.obtener_por_pedido(pedido_id, db)
    if not nota:
        raise HTTPException(status_code=404, detail="Este pedido no tiene nota de crédito asociada")
    return nota
