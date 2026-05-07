"""
Router para gestión de Cotizaciones.
"""
from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from database.database import get_db
from database import models
from schemas.cotizacion import (
    CotizacionCreate, CotizacionUpdate,
    CotizacionResponse, CotizacionListResponse,
    CotizacionVersionCreate, CotizacionVersionResponse,
)
from routers.auth import get_current_active_user
from services.tenant_service import obtener_siguiente_numero_cotizacion, obtener_siguiente_numero_pedido, obtener_siguiente_numero_ot
from services.webhook_service import trigger_cotizacion_creada, trigger_cotizacion_enviada, trigger_cotizacion_aceptada
from routers.pedidos import descontar_inventario


class AceptarCotizacionRequest(BaseModel):
    tipo_documento_id: int
    tipo_pedido_id: int = 1
    local_despacho_id: Optional[int] = None
    local_fabricacion_id: Optional[int] = None
    notas: Optional[str] = None
    medio_pago_id: Optional[int] = None
    requiere_delivery: bool = False
    costo_delivery: Optional[float] = None

router = APIRouter()


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _get_cotizacion(db: Session, cotizacion_id: int, tenant_id: int) -> models.Cotizacion:
    cot = db.query(models.Cotizacion).options(
        joinedload(models.Cotizacion.cliente),
        joinedload(models.Cotizacion.canal_venta),
        joinedload(models.Cotizacion.estado_cotizacion),
        joinedload(models.Cotizacion.version_activa).joinedload(models.CotizacionVersion.creado_por),
        joinedload(models.Cotizacion.versiones).joinedload(models.CotizacionVersion.creado_por),
        joinedload(models.Cotizacion.log).joinedload(models.CotizacionLog.usuario),
        joinedload(models.Cotizacion.log).joinedload(models.CotizacionLog.version),
    ).filter(
        models.Cotizacion.id == cotizacion_id,
        models.Cotizacion.tenant_id == tenant_id,
    ).first()
    if not cot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    return cot


def _registrar_log(db: Session, cotizacion_id: int, accion: str,
                   usuario_id: Optional[int] = None, version_id: Optional[int] = None,
                   detalle: Optional[str] = None):
    db.add(models.CotizacionLog(
        cotizacion_id=cotizacion_id,
        accion=accion,
        usuario_id=usuario_id,
        version_id=version_id,
        detalle=detalle,
    ))


def _estado_by_codigo(db: Session, codigo: str) -> models.EstadoCotizacion:
    est = db.query(models.EstadoCotizacion).filter(models.EstadoCotizacion.codigo == codigo).first()
    if not est:
        raise HTTPException(status_code=500, detail=f"Estado '{codigo}' no encontrado en la BD")
    return est


# --------------------------------------------------
# LISTAR
# --------------------------------------------------

@router.get("/", response_model=List[CotizacionListResponse])
def listar_cotizaciones(
    estado_codigo: Optional[str] = None,
    cliente_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista cotizaciones del tenant con filtros opcionales."""
    query = db.query(models.Cotizacion).options(
        joinedload(models.Cotizacion.cliente),
        joinedload(models.Cotizacion.canal_venta),
        joinedload(models.Cotizacion.estado_cotizacion),
        joinedload(models.Cotizacion.version_activa),
    ).filter(models.Cotizacion.tenant_id == current_user.tenant_id)

    if estado_codigo:
        query = query.join(models.EstadoCotizacion).filter(
            models.EstadoCotizacion.codigo == estado_codigo
        )
    if cliente_id:
        query = query.filter(models.Cotizacion.cliente_id == cliente_id)

    cotizaciones = query.order_by(models.Cotizacion.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for cot in cotizaciones:
        item = CotizacionListResponse(
            id=cot.id,
            numero_cotizacion=cot.numero_cotizacion,
            cliente=cot.cliente,
            canal_venta=cot.canal_venta,
            estado_cotizacion=cot.estado_cotizacion,
            fecha_vencimiento=cot.fecha_vencimiento,
            monto_total=float(cot.version_activa.monto_total) if cot.version_activa else None,
            created_at=cot.created_at,
        )
        result.append(item)
    return result


# --------------------------------------------------
# OBTENER DETALLE
# --------------------------------------------------

@router.get("/{cotizacion_id}", response_model=CotizacionResponse)
def obtener_cotizacion(
    cotizacion_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retorna el detalle completo: versiones + log."""
    return _get_cotizacion(db, cotizacion_id, current_user.tenant_id)


# --------------------------------------------------
# CREAR
# --------------------------------------------------

@router.post("/", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
def crear_cotizacion(
    data: CotizacionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Crea una cotización con su versión inicial (v1).
    La versión 1 representa la solicitud original del cliente y nunca se modifica.
    """
    # Validar cliente
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == data.cliente_id,
        models.Cliente.tenant_id == current_user.tenant_id,
    ).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="Cliente no encontrado")

    # Estado inicial: BORRADOR
    estado = _estado_by_codigo(db, "BORRADOR")

    # Número correlativo
    numero = obtener_siguiente_numero_cotizacion(db, current_user.tenant_id)

    # Crear cotización madre (sin version_activa_id aún)
    cotizacion = models.Cotizacion(
        tenant_id=current_user.tenant_id,
        cliente_id=data.cliente_id,
        canal_venta_id=data.canal_venta_id,
        numero_cotizacion=numero,
        estado_cotizacion_id=estado.id,
        fecha_vencimiento=data.fecha_vencimiento,
        notas=data.notas,
    )
    db.add(cotizacion)
    db.flush()  # Obtener cotizacion.id

    # Crear versión 1
    items_dict = [item.model_dump() for item in data.items]
    version = models.CotizacionVersion(
        cotizacion_id=cotizacion.id,
        numero_version=1,
        items=items_dict,
        monto_total=data.monto_total,
        creado_por_id=current_user.id,
    )
    db.add(version)
    db.flush()

    # Apuntar version_activa
    cotizacion.version_activa_id = version.id

    # Log
    _registrar_log(db, cotizacion.id, "CREADA", current_user.id, version.id,
                   f"Cotización creada con versión inicial. Monto: ${data.monto_total:,.0f}")

    db.commit()
    db.refresh(cotizacion)
    trigger_cotizacion_creada(cotizacion, db)
    return _get_cotizacion(db, cotizacion.id, current_user.tenant_id)


# --------------------------------------------------
# NUEVA VERSIÓN
# --------------------------------------------------

@router.post("/{cotizacion_id}/versiones", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
def crear_nueva_version(
    cotizacion_id: int,
    data: CotizacionVersionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Crea una nueva versión de la cotización.
    Solo se puede versionar si el estado es BORRADOR o ENVIADA.
    """
    cotizacion = db.query(models.Cotizacion).options(
        joinedload(models.Cotizacion.estado_cotizacion),
        joinedload(models.Cotizacion.versiones),
    ).filter(
        models.Cotizacion.id == cotizacion_id,
        models.Cotizacion.tenant_id == current_user.tenant_id,
    ).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if cotizacion.estado_cotizacion.codigo not in ("BORRADOR", "ENVIADA"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede versionar una cotización en estado '{cotizacion.estado_cotizacion.nombre}'"
        )

    siguiente = len(cotizacion.versiones) + 1
    items_dict = [item.model_dump() for item in data.items]
    nueva_version = models.CotizacionVersion(
        cotizacion_id=cotizacion_id,
        numero_version=siguiente,
        items=items_dict,
        monto_total=data.monto_total,
        motivo_cambio=data.motivo_cambio,
        creado_por_id=current_user.id,
    )
    db.add(nueva_version)
    db.flush()

    cotizacion.version_activa_id = nueva_version.id

    # Retroceder a BORRADOR para que pueda enviarse la nueva versión al cliente
    if cotizacion.estado_cotizacion.codigo == "ENVIADA":
        cotizacion.estado_cotizacion_id = _estado_by_codigo(db, "BORRADOR").id

    _registrar_log(db, cotizacion_id, "VERSION_CREADA", current_user.id, nueva_version.id,
                   data.motivo_cambio or f"Versión {siguiente} creada. Monto: ${data.monto_total:,.0f}")

    db.commit()
    return _get_cotizacion(db, cotizacion_id, current_user.tenant_id)


# --------------------------------------------------
# CAMBIAR ESTADO
# --------------------------------------------------

@router.patch("/{cotizacion_id}/estado", response_model=CotizacionResponse)
def cambiar_estado(
    cotizacion_id: int,
    nuevo_estado_codigo: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Cambia el estado de la cotización. Valida transiciones permitidas."""
    cotizacion = db.query(models.Cotizacion).options(
        joinedload(models.Cotizacion.estado_cotizacion),
    ).filter(
        models.Cotizacion.id == cotizacion_id,
        models.Cotizacion.tenant_id == current_user.tenant_id,
    ).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    estado_actual = cotizacion.estado_cotizacion.codigo

    # Transiciones válidas
    TRANSICIONES = {
        "BORRADOR":  ["ENVIADA", "RECHAZADA"],
        "ENVIADA":   ["ACEPTADA", "RECHAZADA", "VENCIDA"],
    }

    if estado_actual not in TRANSICIONES or nuevo_estado_codigo not in TRANSICIONES[estado_actual]:
        raise HTTPException(
            status_code=400,
            detail=f"Transición no permitida: {estado_actual} → {nuevo_estado_codigo}"
        )

    nuevo_estado = _estado_by_codigo(db, nuevo_estado_codigo)
    cotizacion.estado_cotizacion_id = nuevo_estado.id

    _registrar_log(db, cotizacion_id, nuevo_estado_codigo, current_user.id,
                   detalle=f"Estado cambiado de {estado_actual} a {nuevo_estado_codigo}")

    db.commit()
    db.refresh(cotizacion)
    if nuevo_estado_codigo == "ENVIADA":
        trigger_cotizacion_enviada(cotizacion, db)
    return _get_cotizacion(db, cotizacion_id, current_user.tenant_id)


# --------------------------------------------------
# ACEPTAR (flujo completo — se expande en Etapa 7)
# --------------------------------------------------

@router.post("/{cotizacion_id}/aceptar", response_model=CotizacionResponse)
def aceptar_cotizacion(
    cotizacion_id: int,
    data: AceptarCotizacionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Acepta la cotización y genera el Pedido.
    - Si hay stock suficiente → Pedido CONFIRMADO
    - Si falta stock en algún ítem → crea OT tipo OP con los ítems faltantes, Pedido queda PENDIENTE
    """
    cotizacion = db.query(models.Cotizacion).options(
        joinedload(models.Cotizacion.estado_cotizacion),
        joinedload(models.Cotizacion.version_activa),
        joinedload(models.Cotizacion.cliente),
        joinedload(models.Cotizacion.canal_venta),
    ).filter(
        models.Cotizacion.id == cotizacion_id,
        models.Cotizacion.tenant_id == current_user.tenant_id,
    ).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if cotizacion.estado_cotizacion.codigo not in ("BORRADOR", "ENVIADA"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede aceptar una cotización en estado '{cotizacion.estado_cotizacion.nombre}'"
        )
    if not cotizacion.version_activa or not cotizacion.version_activa.items:
        raise HTTPException(status_code=400, detail="La cotización no tiene ítems en la versión activa")

    # Validar tipo_documento y tipo_pedido
    if not db.query(models.TipoDocumento).filter(models.TipoDocumento.id == data.tipo_documento_id).first():
        raise HTTPException(status_code=400, detail="Tipo de documento inválido")
    if not db.query(models.TipoPedido).filter(models.TipoPedido.id == data.tipo_pedido_id).first():
        raise HTTPException(status_code=400, detail="Tipo de pedido inválido")

    # Local de fabricación del tenant (para chequeo de stock y OT)
    locales_fab = db.query(models.Local).filter(
        models.Local.tenant_id == current_user.tenant_id,
        models.Local.es_local_fabricacion == True,
        models.Local.activo == True,
    ).all()

    if len(locales_fab) == 0:
        raise HTTPException(
            status_code=400,
            detail="No hay locales de fabricación configurados. Configura al menos uno en Administración > Locales antes de aceptar cotizaciones.",
        )
    elif len(locales_fab) == 1:
        local_fab = locales_fab[0]
    else:
        if not data.local_fabricacion_id:
            nombres = ", ".join(f"'{l.nombre}'" for l in locales_fab)
            raise HTTPException(
                status_code=400,
                detail=f"Hay múltiples locales de fabricación ({nombres}). Debes seleccionar en cuál se producirá.",
            )
        local_fab = next((l for l in locales_fab if l.id == data.local_fabricacion_id), None)
        if not local_fab:
            raise HTTPException(
                status_code=400,
                detail="El local de fabricación seleccionado no es válido o no está activo.",
            )

    # Local del pedido: local_despacho_id si se indica, sino el local de fabricación, sino el primero activo
    local_pedido = (
        db.query(models.Local).filter(models.Local.id == data.local_despacho_id, models.Local.tenant_id == current_user.tenant_id).first()
        if data.local_despacho_id else local_fab
    )
    if not local_pedido:
        local_pedido = db.query(models.Local).filter(
            models.Local.tenant_id == current_user.tenant_id,
            models.Local.activo == True,
        ).first()
    if not local_pedido:
        raise HTTPException(status_code=400, detail="No hay locales activos configurados para el tenant")

    items_version = cotizacion.version_activa.items  # lista de dicts [{producto_id, nombre, cantidad, precio_unitario, subtotal}]

    # ── Chequeo de stock ──────────────────────────────────────────────────────
    items_sin_stock = []
    if local_fab:
        for item in items_version:
            inv = db.query(models.Inventario).filter(
                models.Inventario.producto_id == item["producto_id"],
                models.Inventario.local_id == local_fab.id,
            ).first()
            stock = float(inv.cantidad_stock) if inv else 0.0
            if stock < float(item["cantidad"]):
                items_sin_stock.append({
                    "producto_id": item["producto_id"],
                    "nombre": item.get("nombre", ""),
                    "cantidad_faltante": float(item["cantidad"]) - stock,
                })

    # ── Crear Pedido ──────────────────────────────────────────────────────────
    estado_pendiente = db.query(models.EstadoPedido).filter(models.EstadoPedido.codigo == "PENDIENTE").first()
    estado_confirmado = db.query(models.EstadoPedido).filter(models.EstadoPedido.codigo == "CONFIRMADO").first()

    numero_pedido = obtener_siguiente_numero_pedido(db, current_user.tenant_id)

    # ── Resolver medio de pago ────────────────────────────────────────────────
    medio_pago = None
    if data.medio_pago_id:
        medio_pago = db.query(models.MedioPago).filter(models.MedioPago.id == data.medio_pago_id).first()

    pedido = models.Pedido(
        tenant_id=current_user.tenant_id,
        numero_pedido=numero_pedido,
        cliente_id=cotizacion.cliente_id,
        local_id=local_pedido.id,
        local_despacho_id=data.local_despacho_id,
        tipo_pedido_id=data.tipo_pedido_id,
        tipo_documento_tributario_id=data.tipo_documento_id,
        canal_venta_id=cotizacion.canal_venta_id,
        usuario_id=current_user.id,
        medio_pago_id=data.medio_pago_id,
        estado_id=estado_pendiente.id if items_sin_stock else estado_confirmado.id,
        monto_total=float(cotizacion.version_activa.monto_total),
        cotizacion_id=cotizacion.id,
        notas=data.notas,
        inventario_descontado=False,
        costo_delivery=float(data.costo_delivery) if data.requiere_delivery and data.costo_delivery is not None else None,
    )
    db.add(pedido)
    db.flush()

    # Ítems del pedido desde la versión activa
    for item in items_version:
        db.add(models.ItemPedido(
            pedido_id=pedido.id,
            producto_id=item["producto_id"],
            cantidad=float(item["cantidad"]),
            precio_unitario_venta=float(item["precio_unitario"]),
        ))
    db.flush()  # Necesario para que pedido.items esté disponible antes de descontar

    # ── Si hay stock suficiente → descontar inventario inmediatamente ────────
    if not items_sin_stock and local_fab:
        descontar_inventario(pedido, local_fab.id, db)

    # ── Lógica de cobro según medio de pago ──────────────────────────────────
    if medio_pago:
        if medio_pago.es_contado or (not medio_pago.permite_cheque and medio_pago.plazo_dias == 0):
            # Pago al contado → marcar como pagado inmediatamente
            pedido.es_pagado = True
        elif not medio_pago.permite_cheque and medio_pago.plazo_dias > 0:
            # Pago diferido (ej: transferencia a X días) → crear CobroPendiente
            from datetime import timedelta
            fecha_venc = datetime.now(timezone.utc) + timedelta(days=medio_pago.plazo_dias)
            db.add(models.CobroPendiente(
                tenant_id=current_user.tenant_id,
                pedido_id=pedido.id,
                monto=float(cotizacion.version_activa.monto_total) + (float(data.costo_delivery) if data.requiere_delivery and data.costo_delivery else 0),
                fecha_vencimiento=fecha_venc,
                estado="PENDIENTE",
            ))
        # Si permite_cheque: se registran los cheques manualmente desde el pedido

    # ── Si faltan ítems → crear OT tipo OP ───────────────────────────────────
    ot_id = None
    if items_sin_stock and local_fab:
        tipo_op = db.query(models.TipoOT).filter(models.TipoOT.codigo == "OP").first()
        estado_ot_pendiente = db.query(models.EstadoOT).filter(models.EstadoOT.codigo == "PENDIENTE").first()
        primera_etapa = db.query(models.OtEtapaTipo).filter(
            models.OtEtapaTipo.tenant_id == current_user.tenant_id,
            models.OtEtapaTipo.tipo_ot_id == tipo_op.id,
            models.OtEtapaTipo.activo == True,
        ).order_by(models.OtEtapaTipo.orden).first() if tipo_op else None

        if tipo_op and estado_ot_pendiente:
            numero_ot = obtener_siguiente_numero_ot(db, current_user.tenant_id)
            ot = models.OrdenTrabajo(
                tenant_id=current_user.tenant_id,
                numero_ot=numero_ot,
                tipo_ot_id=tipo_op.id,
                estado_ot_id=estado_ot_pendiente.id,
                etapa_actual_id=primera_etapa.id if primera_etapa else None,
                local_id=local_fab.id,
                pedido_id=pedido.id,
                cotizacion_id=cotizacion.id,
                notas=f"Generada al aceptar cotización {cotizacion.numero_cotizacion}",
                creado_por_id=current_user.id,
            )
            db.add(ot)
            db.flush()

            for item_faltante in items_sin_stock:
                db.add(models.OtItem(
                    ot_id=ot.id,
                    producto_id=item_faltante["producto_id"],
                    cantidad=item_faltante["cantidad_faltante"],
                ))

            # OP vinculada automáticamente
            unidad_default = db.query(models.UnidadMedida).filter(models.UnidadMedida.activo == True).first()
            op = models.OrdenProduccion(
                local_id=local_fab.id,
                fecha_programada=datetime.now(timezone.utc),
                notas=f"Generada desde cotización {cotizacion.numero_cotizacion}",
                estado="PLANIFICADA",
            )
            db.add(op)
            db.flush()
            for item_faltante in items_sin_stock:
                if unidad_default:
                    db.add(models.DetalleOrdenProduccion(
                        orden_id=op.id,
                        producto_id=item_faltante["producto_id"],
                        unidad_medida_id=unidad_default.id,
                        cantidad_programada=item_faltante["cantidad_faltante"],
                    ))
            ot.op_id = op.id
            ot_id = ot.id

            db.add(models.OtLog(
                ot_id=ot.id,
                accion="CREADA",
                etapa_id=primera_etapa.id if primera_etapa else None,
                usuario_id=current_user.id,
                detalle=f"OT generada automáticamente al aceptar cotización {cotizacion.numero_cotizacion}",
            ))

    # ── Marcar cotización ACEPTADA ────────────────────────────────────────────
    cotizacion.version_activa.es_version_aceptada = True
    cotizacion.estado_cotizacion_id = _estado_by_codigo(db, "ACEPTADA").id

    detalle_log = f"Cotización aceptada → Pedido {numero_pedido} generado"
    if ot_id:
        detalle_log += f" | Stock insuficiente → OT generada (ID {ot_id})"

    _registrar_log(db, cotizacion_id, "ACEPTADA", current_user.id,
                   version_id=cotizacion.version_activa_id,
                   detalle=detalle_log)

    db.commit()
    db.refresh(cotizacion)
    estado_pedido_str = "PENDIENTE" if items_sin_stock else "CONFIRMADO"
    costo_delivery_val = float(data.costo_delivery) if data.requiere_delivery and data.costo_delivery is not None else None
    trigger_cotizacion_aceptada(cotizacion, db, numero_pedido, estado_pedido_str, costo_delivery_val)
    return _get_cotizacion(db, cotizacion_id, current_user.tenant_id)


# --------------------------------------------------
# ACTUALIZAR (notas, fecha vencimiento, canal)
# --------------------------------------------------

@router.put("/{cotizacion_id}", response_model=CotizacionResponse)
def actualizar_cotizacion(
    cotizacion_id: int,
    data: CotizacionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    cotizacion = db.query(models.Cotizacion).filter(
        models.Cotizacion.id == cotizacion_id,
        models.Cotizacion.tenant_id == current_user.tenant_id,
    ).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cotizacion, field, value)

    db.commit()
    return _get_cotizacion(db, cotizacion_id, current_user.tenant_id)
