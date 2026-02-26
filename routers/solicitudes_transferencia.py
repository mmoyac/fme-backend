"""
Router para Solicitudes de Transferencia entre locales.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import SolicitudTransferencia, ItemSolicitudTransferencia
from services.tenant_service import get_tenant_from_request
from schemas.solicitud_transferencia import (
    SolicitudTransferenciaCreate,
    SolicitudTransferenciaUpdate,
    SolicitudTransferenciaResponse,
    ItemSolicitudTransferenciaResponse
)

router = APIRouter(prefix="/api/solicitudes-transferencia", tags=["SolicitudesTransferencia"])

@router.post("/", response_model=SolicitudTransferenciaResponse, status_code=status.HTTP_201_CREATED)
def crear_solicitud_transferencia(data: SolicitudTransferenciaCreate, db: Session = Depends(get_db)):
    solicitud = SolicitudTransferencia(
        tenant_id=data.tenant_id,
        local_origen_id=data.local_origen_id,
        local_destino_id=data.local_destino_id,
        usuario_solicitante_id=data.usuario_solicitante_id,
        estado_id=data.estado_id,
        nota=data.nota
    )
    db.add(solicitud)
    db.flush()  # Para obtener el ID antes de agregar los items
    items = []
    for item in data.items:
        item_obj = ItemSolicitudTransferencia(
            solicitud_id=solicitud.solicitud_id,
            producto_id=item.producto_id,
            cantidad_solicitada=item.cantidad_solicitada,
            cantidad_aprobada=item.cantidad_aprobada
        )
        db.add(item_obj)
        items.append(item_obj)
    db.commit()
    db.refresh(solicitud)
    return SolicitudTransferenciaResponse(
        solicitud_id=solicitud.solicitud_id,
        tenant_id=solicitud.tenant_id,
        local_origen_id=solicitud.local_origen_id,
        local_destino_id=solicitud.local_destino_id,
        usuario_solicitante_id=solicitud.usuario_solicitante_id,
        estado_id=solicitud.estado_id,
        nota=solicitud.nota,
        fecha_creacion=solicitud.fecha_creacion,
        fecha_actualizacion=solicitud.fecha_actualizacion,
        items=[ItemSolicitudTransferenciaResponse(
            solicitud_item_id=i.solicitud_item_id,
            producto_id=i.producto_id,
            cantidad_solicitada=i.cantidad_solicitada,
            cantidad_aprobada=i.cantidad_aprobada,
            movimiento_inventario_id=i.movimiento_inventario_id
        ) for i in items]
    )

@router.get("/", response_model=List[SolicitudTransferenciaResponse])
def listar_solicitudes_transferencia(request: Request, db: Session = Depends(get_db)):
    tenant = get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    solicitudes = db.query(SolicitudTransferencia).filter(SolicitudTransferencia.tenant_id == tenant.id).all()
    result = []
    for s in solicitudes:
        result.append(SolicitudTransferenciaResponse(
            solicitud_id=s.solicitud_id,
            tenant_id=s.tenant_id,
            local_origen_id=s.local_origen_id,
            local_destino_id=s.local_destino_id,
            usuario_solicitante_id=s.usuario_solicitante_id,
            estado_id=s.estado_id,
            nota=s.nota,
            fecha_creacion=s.fecha_creacion,
            fecha_actualizacion=s.fecha_actualizacion,
            items=[ItemSolicitudTransferenciaResponse(
                solicitud_item_id=i.solicitud_item_id,
                producto_id=i.producto_id,
                cantidad_solicitada=i.cantidad_solicitada,
                cantidad_aprobada=i.cantidad_aprobada,
                movimiento_inventario_id=i.movimiento_inventario_id
            ) for i in s.items]
        ))
    return result

@router.get("/{solicitud_id}", response_model=SolicitudTransferenciaResponse)
def obtener_solicitud_transferencia(solicitud_id: int, db: Session = Depends(get_db)):
    s = db.query(SolicitudTransferencia).filter_by(solicitud_id=solicitud_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return SolicitudTransferenciaResponse(
        solicitud_id=s.solicitud_id,
        tenant_id=s.tenant_id,
        local_origen_id=s.local_origen_id,
        local_destino_id=s.local_destino_id,
        usuario_solicitante_id=s.usuario_solicitante_id,
        estado_id=s.estado_id,
        nota=s.nota,
        fecha_creacion=s.fecha_creacion,
        fecha_actualizacion=s.fecha_actualizacion,
        items=[ItemSolicitudTransferenciaResponse(
            solicitud_item_id=i.solicitud_item_id,
            producto_id=i.producto_id,
            cantidad_solicitada=i.cantidad_solicitada,
            cantidad_aprobada=i.cantidad_aprobada,
            movimiento_inventario_id=i.movimiento_inventario_id
        ) for i in s.items]
    )

@router.put("/{solicitud_id}", response_model=SolicitudTransferenciaResponse)
def actualizar_solicitud_transferencia(solicitud_id: int, data: SolicitudTransferenciaUpdate, db: Session = Depends(get_db)):
    s = db.query(SolicitudTransferencia).filter_by(solicitud_id=solicitud_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if data.estado_id is not None:
        s.estado_id = data.estado_id
    if data.nota is not None:
        s.nota = data.nota
    # Si se envían items, reemplazar todos los items existentes
    if data.items is not None:
        # Eliminar todos los items actuales
        db.query(ItemSolicitudTransferencia).filter_by(solicitud_id=solicitud_id).delete()
        # Agregar los nuevos items
        for item in data.items:
            item_obj = ItemSolicitudTransferencia(
                solicitud_id=s.solicitud_id,
                producto_id=item.producto_id,
                cantidad_solicitada=item.cantidad_solicitada,
                cantidad_aprobada=item.cantidad_aprobada
            )
            db.add(item_obj)
    db.commit()
    db.refresh(s)
    return obtener_solicitud_transferencia(solicitud_id, db)

@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_solicitud_transferencia(solicitud_id: int, db: Session = Depends(get_db)):
    s = db.query(SolicitudTransferencia).filter_by(solicitud_id=solicitud_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    db.delete(s)
    db.commit()
    return None
