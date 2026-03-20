"""
Router para Solicitudes de Transferencia entre locales.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from database.models import User
from routers.auth import get_current_active_user
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import SolicitudTransferencia, ItemSolicitudTransferencia, MovimientoInventario, Inventario
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
                cantidad_recibida=i.cantidad_recibida,
                movimiento_inventario_id=i.movimiento_inventario_id
            ) for i in items],
            usuario_finalizador_id=solicitud.usuario_finalizador_id
        )

@router.get("/", response_model=List[SolicitudTransferenciaResponse])
def listar_solicitudes_transferencia(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    tenant = get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'
    q = db.query(SolicitudTransferencia).filter(SolicitudTransferencia.tenant_id == tenant.id)
    if not es_admin and current_user.local_defecto_id:
        q = q.filter(
            (SolicitudTransferencia.local_origen_id == current_user.local_defecto_id) |
            (SolicitudTransferencia.local_destino_id == current_user.local_defecto_id)
        )
    solicitudes = q.order_by(SolicitudTransferencia.solicitud_id.desc()).all()
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
                cantidad_recibida=i.cantidad_recibida,
                movimiento_inventario_id=i.movimiento_inventario_id
            ) for i in s.items],
            usuario_finalizador_id=s.usuario_finalizador_id,
            recibido=s.recibido,
            usuario_receptor_id=s.usuario_receptor_id,
            fecha_recepcion=s.fecha_recepcion
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
            cantidad_recibida=i.cantidad_recibida,
            movimiento_inventario_id=i.movimiento_inventario_id
        ) for i in s.items],
        usuario_finalizador_id=s.usuario_finalizador_id,
        recibido=s.recibido,
        usuario_receptor_id=s.usuario_receptor_id,
        fecha_recepcion=s.fecha_recepcion
    )

@router.put("/{solicitud_id}", response_model=SolicitudTransferenciaResponse)
def actualizar_solicitud_transferencia(
    solicitud_id: int,
    data: SolicitudTransferenciaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    s = db.query(SolicitudTransferencia).filter_by(solicitud_id=solicitud_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    # Estados: 1=PENDIENTE, 2=EN_PROCESO, 3=FINALIZADO (ajusta según tus IDs reales)
    ESTADO_PENDIENTE = 1
    ESTADO_EN_PROCESO = 2
    ESTADO_FINALIZADO = 3

    # Si está FINALIZADO, solo el local destino puede registrar/actualizar la recepción
    if s.estado_id == ESTADO_FINALIZADO:
        if current_user.local_defecto_id != s.local_destino_id:
            raise HTTPException(status_code=403, detail="Solo el local destino puede registrar la recepción.")
        # Permitir registrar o actualizar la recepción (incluso si ya estaba recibida)
        era_recibido = s.recibido  # guardar estado antes de modificar
        s.recibido = True
        s.usuario_receptor_id = current_user.id
        from datetime import datetime as dt
        s.fecha_recepcion = dt.now()
        # Actualizar cantidades recibidas por ítem y ajustar inventario por diferencia
        if data.items is not None:
            for item_data in data.items:
                item_db = next((i for i in s.items if i.producto_id == item_data.producto_id), None)
                if item_db and item_data.cantidad_recibida is not None:
                    aprobada = item_db.cantidad_aprobada or 0
                    recibida_anterior = item_db.cantidad_recibida or 0
                    recibida_nueva = item_data.cantidad_recibida
                    diferencia = aprobada - recibida_nueva
                    ajuste = recibida_anterior - recibida_nueva  # ajuste por actualización

                    if not era_recibido:
                        # Primera recepción: devolver diferencia al origen
                        if diferencia > 0:
                            inv_origen = db.query(Inventario).filter_by(producto_id=item_db.producto_id, local_id=s.local_origen_id).first()
                            if not inv_origen:
                                inv_origen = Inventario(producto_id=item_db.producto_id, local_id=s.local_origen_id, cantidad_stock=0)
                                db.add(inv_origen)
                            inv_origen.cantidad_stock = (inv_origen.cantidad_stock or 0) + diferencia

                            inv_destino = db.query(Inventario).filter_by(producto_id=item_db.producto_id, local_id=s.local_destino_id).first()
                            if inv_destino:
                                inv_destino.cantidad_stock = (inv_destino.cantidad_stock or 0) - diferencia
                    else:
                        # Actualización de recepción ya registrada: ajustar por cambio
                        if ajuste != 0:
                            inv_origen = db.query(Inventario).filter_by(producto_id=item_db.producto_id, local_id=s.local_origen_id).first()
                            if inv_origen:
                                inv_origen.cantidad_stock = (inv_origen.cantidad_stock or 0) + ajuste
                            inv_destino = db.query(Inventario).filter_by(producto_id=item_db.producto_id, local_id=s.local_destino_id).first()
                            if inv_destino:
                                inv_destino.cantidad_stock = (inv_destino.cantidad_stock or 0) - ajuste

                    item_db.cantidad_recibida = recibida_nueva
        db.commit()
        db.refresh(s)
        return obtener_solicitud_transferencia(solicitud_id, db)

    # Si está EN_PROCESO, solo el local origen puede editar (responder y finalizar)
    if s.estado_id == ESTADO_EN_PROCESO:
        if current_user.local_defecto_id != s.local_origen_id:
            raise HTTPException(status_code=403, detail="Solo el local origen puede editar una solicitud en proceso.")

    # Si está PENDIENTE, solo el local destino (solicitante) puede editar (nota/items, sin cantidades aprobadas)
    if s.estado_id == ESTADO_PENDIENTE:
        if current_user.local_defecto_id == s.local_destino_id:
            # Puede editar nota/items, pero no cantidades aprobadas ni estado
            if data.estado_id is not None and data.estado_id != ESTADO_PENDIENTE:
                raise HTTPException(status_code=403, detail="No puedes cambiar el estado de la solicitud.")
            if data.items is not None:
                for item in data.items:
                    if item.cantidad_aprobada is not None:
                        raise HTTPException(status_code=403, detail="No puedes aprobar cantidades desde el local destino.")
            if data.nota is not None:
                s.nota = data.nota
            if data.items is not None:
                db.query(ItemSolicitudTransferencia).filter_by(solicitud_id=solicitud_id).delete()
                for item in data.items:
                    item_obj = ItemSolicitudTransferencia(
                        solicitud_id=s.solicitud_id,
                        producto_id=item.producto_id,
                        cantidad_solicitada=item.cantidad_solicitada,
                        cantidad_aprobada=None
                    )
                    db.add(item_obj)
            db.commit()
            db.refresh(s)
            return obtener_solicitud_transferencia(solicitud_id, db)
        elif current_user.local_defecto_id == s.local_origen_id:
            # El local origen puede mover a EN_PROCESO (toma la solicitud)
            if data.estado_id == ESTADO_EN_PROCESO:
                s.estado_id = ESTADO_EN_PROCESO
                db.commit()
                db.refresh(s)
                return obtener_solicitud_transferencia(solicitud_id, db)
            else:
                raise HTTPException(status_code=400, detail="Solo puedes tomar la solicitud (EN_PROCESO) desde el local origen.")
        else:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar esta solicitud.")

    # Si está EN_PROCESO y el usuario es del local origen, puede editar cantidades aprobadas y finalizar
    if s.estado_id == ESTADO_EN_PROCESO and current_user.local_defecto_id == s.local_origen_id:
        if data.estado_id == ESTADO_FINALIZADO:
            s.estado_id = ESTADO_FINALIZADO
            s.usuario_finalizador_id = current_user.id
            # Actualizar cantidad_aprobada desde el payload antes de procesar inventario
            if data.items:
                for item_data in data.items:
                    item_db = next((i for i in s.items if i.producto_id == item_data.producto_id), None)
                    if item_db and item_data.cantidad_aprobada is not None:
                        item_db.cantidad_aprobada = item_data.cantidad_aprobada
            # Realizar movimientos de inventario por cada item aprobado
            db.flush()  # Asegura que s.items esté actualizado
            for item in s.items:
                if item.cantidad_aprobada and item.cantidad_aprobada > 0:
                    # Crear movimiento de inventario tipo TRANSFERENCIA
                    movimiento = MovimientoInventario(
                        producto_id=item.producto_id,
                        local_origen_id=s.local_origen_id,
                        local_destino_id=s.local_destino_id,
                        cantidad=item.cantidad_aprobada,
                        tipo_movimiento="TRANSFERENCIA",
                        referencia_id=s.solicitud_id,
                        notas=f"Transferencia por solicitud #{s.solicitud_id}",
                        usuario=str(current_user.id)
                    )
                    db.add(movimiento)
                    db.flush()  # Para obtener el ID
                    # Actualizar inventario origen
                    inv_origen = db.query(Inventario).filter_by(producto_id=item.producto_id, local_id=s.local_origen_id).first()
                    if not inv_origen:
                        inv_origen = Inventario(producto_id=item.producto_id, local_id=s.local_origen_id, cantidad_stock=0)
                        db.add(inv_origen)
                        db.flush()
                    inv_origen.cantidad_stock = (inv_origen.cantidad_stock or 0) - item.cantidad_aprobada
                    # Actualizar inventario destino
                    inv_destino = db.query(Inventario).filter_by(producto_id=item.producto_id, local_id=s.local_destino_id).first()
                    if not inv_destino:
                        inv_destino = Inventario(producto_id=item.producto_id, local_id=s.local_destino_id, cantidad_stock=0)
                        db.add(inv_destino)
                        db.flush()
                    inv_destino.cantidad_stock = (inv_destino.cantidad_stock or 0) + item.cantidad_aprobada
                    # Asignar movimiento al item
                    item.movimiento_inventario_id = movimiento.id
            db.commit()
            db.refresh(s)
            return obtener_solicitud_transferencia(solicitud_id, db)
        if data.nota is not None:
            s.nota = data.nota
        if data.items is not None:
            db.query(ItemSolicitudTransferencia).filter_by(solicitud_id=solicitud_id).delete()
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

    raise HTTPException(status_code=403, detail="No tienes permisos para editar esta solicitud.")

@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_solicitud_transferencia(solicitud_id: int, db: Session = Depends(get_db)):
    s = db.query(SolicitudTransferencia).filter_by(solicitud_id=solicitud_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    db.delete(s)
    db.commit()
    return None
