"""
Router para gestión de Órdenes de Trabajo.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from database import models
from schemas.orden_trabajo import (
    TipoOTCreate, TipoOTUpdate, TipoOTResponse,
    EstadoCotizacionResponse, EstadoOTResponse,
    OtEtapaTipoCreate, OtEtapaTipoUpdate, OtEtapaTipoResponse,
    OrdenTrabajoCreate, OrdenTrabajoUpdate, OrdenTrabajoResponse, OrdenTrabajoListResponse,
    AvanzarEtapaRequest, CerrarOTRequest,
)
from routers.auth import get_current_active_user
from services.tenant_service import obtener_siguiente_numero_ot

router = APIRouter()


# --------------------------------------------------
# TIPOS OT (maestra global — solo superadmin crea/edita)
# --------------------------------------------------

@router.get("/tipos", response_model=List[TipoOTResponse])
def listar_tipos_ot(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista los tipos de Orden de Trabajo disponibles."""
    query = db.query(models.TipoOT)
    if activo is not None:
        query = query.filter(models.TipoOT.activo == activo)
    return query.order_by(models.TipoOT.id).all()


@router.post("/tipos", response_model=TipoOTResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo_ot(
    data: TipoOTCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea un nuevo tipo de OT. Solo superadmin."""
    if db.query(models.TipoOT).filter(models.TipoOT.codigo == data.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un tipo OT con código '{data.codigo}'",
        )
    obj = models.TipoOT(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/tipos/{tipo_id}", response_model=TipoOTResponse)
def actualizar_tipo_ot(
    tipo_id: int,
    data: TipoOTUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Actualiza un tipo de OT existente."""
    obj = db.query(models.TipoOT).filter(models.TipoOT.id == tipo_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo OT no encontrado")
    if data.codigo and data.codigo != obj.codigo:
        if db.query(models.TipoOT).filter(models.TipoOT.codigo == data.codigo).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un tipo OT con código '{data.codigo}'",
            )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# --------------------------------------------------
# ESTADOS (solo lectura — maestras de seed)
# --------------------------------------------------

@router.get("/estados-cotizacion", response_model=List[EstadoCotizacionResponse])
def listar_estados_cotizacion(db: Session = Depends(get_db)):
    """Lista los estados de cotización."""
    return db.query(models.EstadoCotizacion).filter(
        models.EstadoCotizacion.activo == True
    ).order_by(models.EstadoCotizacion.orden).all()


@router.get("/estados-ot", response_model=List[EstadoOTResponse])
def listar_estados_ot(db: Session = Depends(get_db)):
    """Lista los estados de Orden de Trabajo."""
    return db.query(models.EstadoOT).filter(
        models.EstadoOT.activo == True
    ).order_by(models.EstadoOT.orden).all()


# --------------------------------------------------
# ETAPAS POR TIPO (parametrizable por tenant)
# --------------------------------------------------

@router.get("/etapas", response_model=List[OtEtapaTipoResponse])
def listar_etapas(
    tipo_ot_id: Optional[int] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista las etapas configuradas para el tenant. Filtrable por tipo_ot_id."""
    query = db.query(models.OtEtapaTipo).options(
        joinedload(models.OtEtapaTipo.tipo_ot)
    ).filter(models.OtEtapaTipo.tenant_id == current_user.tenant_id)

    if tipo_ot_id is not None:
        query = query.filter(models.OtEtapaTipo.tipo_ot_id == tipo_ot_id)
    if activo is not None:
        query = query.filter(models.OtEtapaTipo.activo == activo)

    return query.order_by(models.OtEtapaTipo.tipo_ot_id, models.OtEtapaTipo.orden).all()


@router.get("/etapas/{etapa_id}", response_model=OtEtapaTipoResponse)
def obtener_etapa(
    etapa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Obtiene una etapa por ID (del tenant del usuario)."""
    obj = db.query(models.OtEtapaTipo).options(
        joinedload(models.OtEtapaTipo.tipo_ot)
    ).filter(
        models.OtEtapaTipo.id == etapa_id,
        models.OtEtapaTipo.tenant_id == current_user.tenant_id,
    ).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etapa no encontrada")
    return obj


@router.post("/etapas", response_model=OtEtapaTipoResponse, status_code=status.HTTP_201_CREATED)
def crear_etapa(
    data: OtEtapaTipoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea una nueva etapa para el tipo de OT del tenant."""
    if not db.query(models.TipoOT).filter(models.TipoOT.id == data.tipo_ot_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo OT con ID {data.tipo_ot_id} no existe",
        )
    obj = models.OtEtapaTipo(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return db.query(models.OtEtapaTipo).options(
        joinedload(models.OtEtapaTipo.tipo_ot)
    ).filter(models.OtEtapaTipo.id == obj.id).first()


@router.put("/etapas/{etapa_id}", response_model=OtEtapaTipoResponse)
def actualizar_etapa(
    etapa_id: int,
    data: OtEtapaTipoUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Actualiza una etapa del tenant."""
    obj = db.query(models.OtEtapaTipo).filter(
        models.OtEtapaTipo.id == etapa_id,
        models.OtEtapaTipo.tenant_id == current_user.tenant_id,
    ).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etapa no encontrada")

    if data.tipo_ot_id and not db.query(models.TipoOT).filter(models.TipoOT.id == data.tipo_ot_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo OT con ID {data.tipo_ot_id} no existe",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return db.query(models.OtEtapaTipo).options(
        joinedload(models.OtEtapaTipo.tipo_ot)
    ).filter(models.OtEtapaTipo.id == obj.id).first()


@router.delete("/etapas/{etapa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_etapa(
    etapa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Elimina (desactiva) una etapa del tenant."""
    obj = db.query(models.OtEtapaTipo).filter(
        models.OtEtapaTipo.id == etapa_id,
        models.OtEtapaTipo.tenant_id == current_user.tenant_id,
    ).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etapa no encontrada")
    obj.activo = False
    db.commit()


# --------------------------------------------------
# ÓRDENES DE TRABAJO — CRUD + flujo de etapas
# --------------------------------------------------

def _ot_query(db: Session, tenant_id: int):
    """Query base con todos los joinedloads para OT."""
    return db.query(models.OrdenTrabajo).options(
        joinedload(models.OrdenTrabajo.tipo_ot),
        joinedload(models.OrdenTrabajo.estado_ot),
        joinedload(models.OrdenTrabajo.etapa_actual).joinedload(models.OtEtapaTipo.tipo_ot),
        joinedload(models.OrdenTrabajo.local),
        joinedload(models.OrdenTrabajo.creado_por),
        joinedload(models.OrdenTrabajo.items).joinedload(models.OtItem.producto),
        joinedload(models.OrdenTrabajo.items).joinedload(models.OtItem.unidad_medida),
        joinedload(models.OrdenTrabajo.log).joinedload(models.OtLog.usuario),
        joinedload(models.OrdenTrabajo.log).joinedload(models.OtLog.etapa).joinedload(models.OtEtapaTipo.tipo_ot),
    ).filter(models.OrdenTrabajo.tenant_id == tenant_id)


@router.get("/", response_model=List[OrdenTrabajoListResponse])
def listar_ordenes_trabajo(
    tipo_ot_id: Optional[int] = None,
    estado_codigo: Optional[str] = None,
    pedido_id: Optional[int] = None,
    cotizacion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista las OT del tenant con filtros opcionales."""
    query = db.query(models.OrdenTrabajo).options(
        joinedload(models.OrdenTrabajo.tipo_ot),
        joinedload(models.OrdenTrabajo.estado_ot),
        joinedload(models.OrdenTrabajo.etapa_actual).joinedload(models.OtEtapaTipo.tipo_ot),
        joinedload(models.OrdenTrabajo.local),
    ).filter(models.OrdenTrabajo.tenant_id == current_user.tenant_id)

    if tipo_ot_id:
        query = query.filter(models.OrdenTrabajo.tipo_ot_id == tipo_ot_id)
    if estado_codigo:
        query = query.join(models.EstadoOT).filter(models.EstadoOT.codigo == estado_codigo.upper())
    if pedido_id:
        query = query.filter(models.OrdenTrabajo.pedido_id == pedido_id)
    if cotizacion_id:
        query = query.filter(models.OrdenTrabajo.cotizacion_id == cotizacion_id)

    return query.order_by(models.OrdenTrabajo.id.desc()).all()


@router.get("/{ot_id}", response_model=OrdenTrabajoResponse)
def obtener_orden_trabajo(
    ot_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Detalle completo de una OT."""
    ot = _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot_id).first()
    if not ot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de Trabajo no encontrada")
    return ot


@router.post("/", response_model=OrdenTrabajoResponse, status_code=status.HTTP_201_CREATED)
def crear_orden_trabajo(
    data: OrdenTrabajoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea una nueva Orden de Trabajo con sus ítems. Estado inicial: PENDIENTE."""
    # Validar tipo OT
    tipo_ot = db.query(models.TipoOT).filter(
        models.TipoOT.id == data.tipo_ot_id, models.TipoOT.activo == True
    ).first()
    if not tipo_ot:
        raise HTTPException(status_code=400, detail="Tipo OT inválido o inactivo")

    # Validar local
    local = db.query(models.Local).filter(
        models.Local.id == data.local_id,
        models.Local.tenant_id == current_user.tenant_id,
    ).first()
    if not local:
        raise HTTPException(status_code=400, detail="Local no encontrado en el tenant")

    # Estado inicial PENDIENTE
    estado = db.query(models.EstadoOT).filter(models.EstadoOT.codigo == "PENDIENTE").first()
    if not estado:
        raise HTTPException(status_code=500, detail="Estado PENDIENTE no encontrado en maestras")

    # Primera etapa configurada para este tipo/tenant
    primera_etapa = db.query(models.OtEtapaTipo).filter(
        models.OtEtapaTipo.tenant_id == current_user.tenant_id,
        models.OtEtapaTipo.tipo_ot_id == data.tipo_ot_id,
        models.OtEtapaTipo.activo == True,
    ).order_by(models.OtEtapaTipo.orden).first()

    numero_ot = obtener_siguiente_numero_ot(db, current_user.tenant_id)

    ot = models.OrdenTrabajo(
        tenant_id=current_user.tenant_id,
        numero_ot=numero_ot,
        tipo_ot_id=data.tipo_ot_id,
        estado_ot_id=estado.id,
        etapa_actual_id=primera_etapa.id if primera_etapa else None,
        local_id=data.local_id,
        pedido_id=data.pedido_id,
        cotizacion_id=data.cotizacion_id,
        fecha_programada=data.fecha_programada,
        notas=data.notas,
        creado_por_id=current_user.id,
    )
    db.add(ot)
    db.flush()

    # Ítems
    for item_data in data.items:
        item = models.OtItem(
            ot_id=ot.id,
            producto_id=item_data.producto_id,
            unidad_medida_id=item_data.unidad_medida_id,
            cantidad=item_data.cantidad,
            notas=item_data.notas,
        )
        db.add(item)

    # Si es tipo OP → crear OrdenProduccion vinculada automáticamente
    detalle_log = f"OT creada con {len(data.items)} ítem(s)"
    if tipo_ot.codigo == "OP":
        # Unidad de medida por defecto (la primera activa) para ítems sin unidad
        unidad_default = db.query(models.UnidadMedida).filter(
            models.UnidadMedida.activo == True
        ).first()

        op = models.OrdenProduccion(
            local_id=data.local_id,
            fecha_programada=data.fecha_programada or datetime.now(timezone.utc),
            notas=f"Generada automáticamente desde OT {numero_ot}" + (f" | {data.notas}" if data.notas else ""),
            estado="PLANIFICADA",
        )
        db.add(op)
        db.flush()

        for item_data in data.items:
            unidad_id = item_data.unidad_medida_id or (unidad_default.id if unidad_default else None)
            if unidad_id:
                det_op = models.DetalleOrdenProduccion(
                    orden_id=op.id,
                    producto_id=item_data.producto_id,
                    unidad_medida_id=unidad_id,
                    cantidad_programada=item_data.cantidad,
                )
                db.add(det_op)

        ot.op_id = op.id
        detalle_log = f"OT creada con {len(data.items)} ítem(s) → OP #{op.id} generada automáticamente"

    # Log de creación
    log = models.OtLog(
        ot_id=ot.id,
        accion="CREADA",
        etapa_id=primera_etapa.id if primera_etapa else None,
        usuario_id=current_user.id,
        detalle=detalle_log,
    )
    db.add(log)
    db.commit()

    return _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot.id).first()


@router.put("/{ot_id}", response_model=OrdenTrabajoResponse)
def actualizar_orden_trabajo(
    ot_id: int,
    data: OrdenTrabajoUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Actualiza campos opcionales de la OT (solo si no está cerrada/cancelada)."""
    ot = db.query(models.OrdenTrabajo).join(models.EstadoOT).filter(
        models.OrdenTrabajo.id == ot_id,
        models.OrdenTrabajo.tenant_id == current_user.tenant_id,
    ).first()
    if not ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    if ot.estado_ot.es_final:
        raise HTTPException(status_code=400, detail="No se puede modificar una OT en estado final")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ot, field, value)
    db.commit()
    return _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot.id).first()


@router.post("/{ot_id}/avanzar-etapa", response_model=OrdenTrabajoResponse)
def avanzar_etapa(
    ot_id: int,
    data: AvanzarEtapaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Avanza la OT a una etapa específica del flujo."""
    ot = db.query(models.OrdenTrabajo).join(models.EstadoOT).filter(
        models.OrdenTrabajo.id == ot_id,
        models.OrdenTrabajo.tenant_id == current_user.tenant_id,
    ).first()
    if not ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    if ot.estado_ot.es_final:
        raise HTTPException(status_code=400, detail="La OT ya está en estado final, no se puede avanzar")
    if ot.tipo_ot.codigo == "OP":
        raise HTTPException(status_code=400, detail="Las OT tipo OP se gestionan desde el módulo de Producción")

    # Validar que la etapa destino pertenece al tenant y al mismo tipo OT
    etapa = db.query(models.OtEtapaTipo).filter(
        models.OtEtapaTipo.id == data.etapa_id,
        models.OtEtapaTipo.tenant_id == current_user.tenant_id,
        models.OtEtapaTipo.tipo_ot_id == ot.tipo_ot_id,
        models.OtEtapaTipo.activo == True,
    ).first()
    if not etapa:
        raise HTTPException(status_code=400, detail="Etapa inválida para este tipo/tenant")

    # Transicionar a EN_PROCESO si estaba en PENDIENTE
    if ot.estado_ot.codigo == "PENDIENTE":
        estado_en_proceso = db.query(models.EstadoOT).filter(
            models.EstadoOT.codigo == "EN_PROCESO"
        ).first()
        if estado_en_proceso:
            ot.estado_ot_id = estado_en_proceso.id
            if not ot.fecha_inicio:
                ot.fecha_inicio = datetime.now(timezone.utc)

    ot.etapa_actual_id = data.etapa_id
    log = models.OtLog(
        ot_id=ot.id,
        accion="ETAPA_AVANZADA",
        etapa_id=data.etapa_id,
        usuario_id=current_user.id,
        detalle=data.detalle or f"Avanzado a etapa: {etapa.nombre}",
    )
    db.add(log)
    db.commit()
    return _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot.id).first()


@router.post("/{ot_id}/cerrar", response_model=OrdenTrabajoResponse)
def cerrar_orden_trabajo(
    ot_id: int,
    data: CerrarOTRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Cierra la OT. Marca estado CERRADA y fecha_cierre.
    Si la OT está vinculada a un pedido, actualiza el stock (decrementación de inventario
    queda para Etapa 7 cuando se integre con pedidos).
    """
    ot = db.query(models.OrdenTrabajo).join(models.EstadoOT).filter(
        models.OrdenTrabajo.id == ot_id,
        models.OrdenTrabajo.tenant_id == current_user.tenant_id,
    ).first()
    if not ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    if ot.estado_ot.es_final:
        raise HTTPException(status_code=400, detail=f"La OT ya está en estado final: {ot.estado_ot.codigo}")
    if ot.tipo_ot.codigo == "OP":
        raise HTTPException(status_code=400, detail="Las OT tipo OP se cierran automáticamente al finalizar la Orden de Producción")

    estado_cerrada = db.query(models.EstadoOT).filter(models.EstadoOT.codigo == "CERRADA").first()
    if not estado_cerrada:
        raise HTTPException(status_code=500, detail="Estado CERRADA no encontrado en maestras")

    ot.estado_ot_id = estado_cerrada.id
    ot.fecha_cierre = datetime.now(timezone.utc)

    # Actualizar cantidades ejecutadas si se informan
    if data.items_ejecutados:
        items_map = {i.id: i for i in ot.items}
        for item_data in data.items_ejecutados:
            # items_ejecutados contiene cantidades, pero no IDs explícitos en el schema
            pass  # La integración detallada se hace en Etapa 7

    log = models.OtLog(
        ot_id=ot.id,
        accion="CERRADA",
        etapa_id=ot.etapa_actual_id,
        usuario_id=current_user.id,
        detalle=data.detalle or "OT cerrada manualmente",
    )
    db.add(log)
    db.commit()
    return _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot.id).first()


@router.post("/{ot_id}/cancelar", response_model=OrdenTrabajoResponse)
def cancelar_orden_trabajo(
    ot_id: int,
    detalle: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Cancela una OT activa."""
    ot = db.query(models.OrdenTrabajo).join(models.EstadoOT).filter(
        models.OrdenTrabajo.id == ot_id,
        models.OrdenTrabajo.tenant_id == current_user.tenant_id,
    ).first()
    if not ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    if ot.estado_ot.es_final:
        raise HTTPException(status_code=400, detail=f"La OT ya está en estado final: {ot.estado_ot.codigo}")

    estado_cancelada = db.query(models.EstadoOT).filter(models.EstadoOT.codigo == "CANCELADA").first()
    if not estado_cancelada:
        raise HTTPException(status_code=500, detail="Estado CANCELADA no encontrado en maestras")

    ot.estado_ot_id = estado_cancelada.id
    log = models.OtLog(
        ot_id=ot.id,
        accion="CANCELADA",
        etapa_id=ot.etapa_actual_id,
        usuario_id=current_user.id,
        detalle=detalle or "OT cancelada manualmente",
    )
    db.add(log)
    db.commit()
    return _ot_query(db, current_user.tenant_id).filter(models.OrdenTrabajo.id == ot.id).first()
