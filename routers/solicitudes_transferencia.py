"""
Router para Solicitudes de Transferencia entre locales.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from database.models import User
from routers.auth import get_current_active_user
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import SolicitudTransferencia, ItemSolicitudTransferencia, MovimientoInventario, Inventario, EstadoEnrolamiento, Local, Producto
from services import notification_service
from schemas.solicitud_transferencia import (
    SolicitudTransferenciaCreate,
    SolicitudTransferenciaUpdate,
    SolicitudTransferenciaResponse,
    ItemSolicitudTransferenciaResponse
)

router = APIRouter(prefix="/api/solicitudes-transferencia", tags=["SolicitudesTransferencia"])


# --------------------------------------------------
# Seguridad (change OpenSpec: fix-seguridad-inventario)
# Todo endpoint exige usuario autenticado y opera solo sobre su tenant.
# --------------------------------------------------

def _es_admin(user: User) -> bool:
    return bool(user.is_superadmin or (user.role and user.role.nombre.lower() == 'admin'))


def _get_solicitud(db: Session, solicitud_id: int, user: User) -> SolicitudTransferencia:
    """Solicitud del tenant del usuario; 404 si no existe o es de otro tenant."""
    s = db.query(SolicitudTransferencia).filter(
        SolicitudTransferencia.solicitud_id == solicitud_id,
        SolicitudTransferencia.tenant_id == user.tenant_id,
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return s


def _validar_pertenencia(db: Session, user: User, local_ids, producto_ids) -> None:
    """Locales y productos deben pertenecer al tenant del usuario (404 si no)."""
    local_ids, producto_ids = set(local_ids), set(producto_ids)
    if local_ids:
        encontrados = {lid for (lid,) in db.query(Local.id).filter(
            Local.id.in_(local_ids), Local.tenant_id == user.tenant_id).all()}
        if encontrados != local_ids:
            raise HTTPException(status_code=404, detail="Local no encontrado")
    if producto_ids:
        encontrados = {pid for (pid,) in db.query(Producto.id).filter(
            Producto.id.in_(producto_ids), Producto.tenant_id == user.tenant_id).all()}
        if encontrados != producto_ids:
            raise HTTPException(status_code=404, detail="Producto no encontrado")


def _serializar(s: SolicitudTransferencia) -> SolicitudTransferenciaResponse:
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
        fecha_recepcion=s.fecha_recepcion,
        requiere_delivery=s.requiere_delivery
    )


def _respuesta(db: Session, solicitud_id: int, user: User) -> SolicitudTransferenciaResponse:
    return _serializar(_get_solicitud(db, solicitud_id, user))


@router.post("/", response_model=SolicitudTransferenciaResponse, status_code=status.HTTP_201_CREATED)
def crear_solicitud_transferencia(
    data: SolicitudTransferenciaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Tenant, solicitante y estado inicial los fija el servidor; se ignora lo que envíe el cliente.
    _validar_pertenencia(
        db, current_user,
        [data.local_origen_id, data.local_destino_id],
        [i.producto_id for i in data.items],
    )
    estado_pendiente = db.query(EstadoEnrolamiento).filter(EstadoEnrolamiento.codigo == 'PENDIENTE').first()
    if not estado_pendiente:
        raise HTTPException(status_code=500, detail="Estado PENDIENTE no configurado")
    solicitud = SolicitudTransferencia(
        tenant_id=current_user.tenant_id,
        local_origen_id=data.local_origen_id,
        local_destino_id=data.local_destino_id,
        usuario_solicitante_id=current_user.id,
        estado_id=estado_pendiente.id,
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

    # Notificar a admins del local origen y superadmins
    local_origen = db.query(Local).filter(Local.id == data.local_origen_id).first()
    solicitante = current_user
    notification_service.notify_solicitud_creada(
        db=db,
        tenant_id=current_user.tenant_id,
        local_origen_id=data.local_origen_id,
        local_origen_nombre=local_origen.nombre if local_origen else f"Local {data.local_origen_id}",
        solicitud_id=solicitud.solicitud_id,
        solicitante_nombre=solicitante.nombre_completo if solicitante else "Usuario",
    )

    return _serializar(solicitud)

@router.get("/", response_model=List[SolicitudTransferenciaResponse])
def listar_solicitudes_transferencia(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Tenant del usuario autenticado (antes se tomaba del hostname)
    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'
    q = db.query(SolicitudTransferencia).filter(SolicitudTransferencia.tenant_id == current_user.tenant_id)
    if not es_admin and current_user.local_defecto_id:
        q = q.filter(
            (SolicitudTransferencia.local_origen_id == current_user.local_defecto_id) |
            (SolicitudTransferencia.local_destino_id == current_user.local_defecto_id)
        )
    solicitudes = q.order_by(SolicitudTransferencia.solicitud_id.desc()).all()
    return [_serializar(x) for x in solicitudes]

@router.get("/{solicitud_id}", response_model=SolicitudTransferenciaResponse)
def obtener_solicitud_transferencia(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _respuesta(db, solicitud_id, current_user)

@router.put("/{solicitud_id}", response_model=SolicitudTransferenciaResponse)
def actualizar_solicitud_transferencia(
    solicitud_id: int,
    data: SolicitudTransferenciaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    s = _get_solicitud(db, solicitud_id, current_user)
    if data.items:
        _validar_pertenencia(db, current_user, [], [i.producto_id for i in data.items])

    # Resolver códigos de estado actual y nuevo desde la BD (nunca IDs hardcodeados)
    estados_map = {e.id: e.codigo for e in db.query(EstadoEnrolamiento).all()}
    codigos_map = {v: k for k, v in estados_map.items()}  # codigo -> id

    estado_actual = estados_map.get(s.estado_id)
    estado_nuevo = estados_map.get(data.estado_id) if data.estado_id else None

    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'

    # FINALIZADO: local destino registra recepción, local origen puede cambiar requiere_delivery
    if estado_actual == 'FINALIZADO':
        # Local origen puede actualizar requiere_delivery sin tocar la recepción
        if (es_admin or current_user.local_defecto_id == s.local_origen_id) and data.requiere_delivery is not None and not data.recibido:
            s.requiere_delivery = data.requiere_delivery
            db.commit()
            db.refresh(s)
            return _respuesta(db, solicitud_id, current_user)
        if not es_admin and current_user.local_defecto_id != s.local_destino_id:
            raise HTTPException(status_code=403, detail="Solo el local destino puede registrar la recepción.")
        era_recibido = s.recibido
        s.recibido = True
        s.usuario_receptor_id = current_user.id
        from datetime import datetime as dt
        s.fecha_recepcion = dt.now()
        if data.items is not None:
            for item_data in data.items:
                item_db = next((i for i in s.items if i.producto_id == item_data.producto_id), None)
                if item_db and item_data.cantidad_recibida is not None:
                    aprobada = item_db.cantidad_aprobada or 0
                    recibida_anterior = item_db.cantidad_recibida or 0
                    recibida_nueva = item_data.cantidad_recibida
                    diferencia = aprobada - recibida_nueva
                    ajuste = recibida_anterior - recibida_nueva
                    if not era_recibido:
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
        return _respuesta(db, solicitud_id, current_user)

    # PENDIENTE: local destino edita, local origen inicia atención, admin puede todo
    if estado_actual == 'PENDIENTE':
        if es_admin or current_user.local_defecto_id == s.local_origen_id:
            # Admin o local origen: puede mover a EN_PROCESO
            if estado_nuevo == 'EN_PROCESO':
                s.estado_id = codigos_map['EN_PROCESO']
                db.commit()
                db.refresh(s)
                local_origen = db.query(Local).filter(Local.id == s.local_origen_id).first()
                notification_service.notify_solicitud_en_proceso(
                    db=db,
                    tenant_id=s.tenant_id,
                    local_destino_id=s.local_destino_id,
                    solicitud_id=s.solicitud_id,
                    local_origen_nombre=local_origen.nombre if local_origen else f"Local {s.local_origen_id}",
                )
                return _respuesta(db, solicitud_id, current_user)
            if data.nota is not None:
                s.nota = data.nota
            db.commit()
            db.refresh(s)
            return _respuesta(db, solicitud_id, current_user)
        elif current_user.local_defecto_id == s.local_destino_id:
            # Local destino: puede editar nota/items, no cambiar estado ni aprobar
            if estado_nuevo is not None and estado_nuevo != 'PENDIENTE':
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
                    db.add(ItemSolicitudTransferencia(
                        solicitud_id=s.solicitud_id,
                        producto_id=item.producto_id,
                        cantidad_solicitada=item.cantidad_solicitada,
                        cantidad_aprobada=None
                    ))
            db.commit()
            db.refresh(s)
            return _respuesta(db, solicitud_id, current_user)
        else:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar esta solicitud.")

    # EN_PROCESO: local origen (o admin) aprueba cantidades y finaliza
    if estado_actual == 'EN_PROCESO':
        if not es_admin and current_user.local_defecto_id != s.local_origen_id:
            raise HTTPException(status_code=403, detail="Solo el local origen puede editar una solicitud en proceso.")
        if estado_nuevo == 'FINALIZADO':
            s.estado_id = codigos_map['FINALIZADO']
            s.usuario_finalizador_id = current_user.id
            if data.requiere_delivery is not None:
                s.requiere_delivery = data.requiere_delivery
            if data.items:
                for item_data in data.items:
                    item_db = next((i for i in s.items if i.producto_id == item_data.producto_id), None)
                    if item_db and item_data.cantidad_aprobada is not None:
                        item_db.cantidad_aprobada = item_data.cantidad_aprobada
            db.flush()
            for item in s.items:
                if item.cantidad_aprobada and item.cantidad_aprobada > 0:
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
                    db.flush()
                    inv_origen = db.query(Inventario).filter_by(producto_id=item.producto_id, local_id=s.local_origen_id).first()
                    if not inv_origen:
                        inv_origen = Inventario(producto_id=item.producto_id, local_id=s.local_origen_id, cantidad_stock=0)
                        db.add(inv_origen)
                        db.flush()
                    inv_origen.cantidad_stock = (inv_origen.cantidad_stock or 0) - item.cantidad_aprobada
                    inv_destino = db.query(Inventario).filter_by(producto_id=item.producto_id, local_id=s.local_destino_id).first()
                    if not inv_destino:
                        inv_destino = Inventario(producto_id=item.producto_id, local_id=s.local_destino_id, cantidad_stock=0)
                        db.add(inv_destino)
                        db.flush()
                    inv_destino.cantidad_stock = (inv_destino.cantidad_stock or 0) + item.cantidad_aprobada
                    item.movimiento_inventario_id = movimiento.id
            db.commit()
            db.refresh(s)
            local_origen = db.query(Local).filter(Local.id == s.local_origen_id).first()
            notification_service.notify_solicitud_finalizada(
                db=db,
                tenant_id=s.tenant_id,
                local_destino_id=s.local_destino_id,
                solicitud_id=s.solicitud_id,
                local_origen_nombre=local_origen.nombre if local_origen else f"Local {s.local_origen_id}",
            )
            return _respuesta(db, solicitud_id, current_user)
        if data.nota is not None:
            s.nota = data.nota
        if data.requiere_delivery is not None:
            s.requiere_delivery = data.requiere_delivery
        if data.items is not None:
            db.query(ItemSolicitudTransferencia).filter_by(solicitud_id=solicitud_id).delete()
            for item in data.items:
                db.add(ItemSolicitudTransferencia(
                    solicitud_id=s.solicitud_id,
                    producto_id=item.producto_id,
                    cantidad_solicitada=item.cantidad_solicitada,
                    cantidad_aprobada=item.cantidad_aprobada
                ))
        db.commit()
        db.refresh(s)
        return _respuesta(db, solicitud_id, current_user)

    raise HTTPException(status_code=403, detail="No tienes permisos para editar esta solicitud.")

@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_solicitud_transferencia(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    s = _get_solicitud(db, solicitud_id, current_user)
    if not (_es_admin(current_user) or s.usuario_solicitante_id == current_user.id):
        raise HTTPException(status_code=403, detail="Solo un admin o quien creó la solicitud puede eliminarla.")
    db.delete(s)
    db.commit()
    return None
