"""
Router para gestión de cobranza: cobros pendientes unificados (cheques + transferencias diferidas).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone

from database.database import get_db
from database.models import (
    CobroPendiente as CobroPendienteModel,
    Pedido as PedidoModel,
    Cheque as ChequeModel,
    EstadoCheque as EstadoChequeModel,
    User,
)
from routers.auth import get_current_active_user
from services.credito_service import CreditoService

router = APIRouter()

ESTADOS_CHEQUE_PENDIENTES = ["PENDIENTE", "DEPOSITADO"]


def _pedido_pertenece_tenant(pedido: PedidoModel, tenant_id: int) -> bool:
    return pedido.tenant_id == tenant_id


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/")
def listar_cobranza(
    estado: Optional[str] = Query(None, description="PENDIENTE | RECIBIDO | VENCIDO | ANULADO"),
    tipo: Optional[str] = Query(None, description="CHEQUE | TRANSFERENCIA"),
    cliente_id: Optional[int] = Query(None),
    local_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista unificada de cobros pendientes del tenant:
    - Pedidos con cheques no totalmente cobrados
    - Pedidos con cobros diferidos (transferencias, etc.)
    """
    tenant_id = current_user.tenant_id
    resultado = []

    # ── 1. CHEQUES ────────────────────────────────────────────────────────────
    if tipo in (None, "CHEQUE"):
        estados_cobrado = db.query(EstadoChequeModel).filter(
            EstadoChequeModel.codigo.in_(["COBRADO", "ANULADO"])
        ).all()
        ids_estados_cobrado = {e.id for e in estados_cobrado}

        # Pedidos del tenant que tienen cheques pendientes
        pedidos_con_cheques = (
            db.query(PedidoModel)
            .filter(
                PedidoModel.tenant_id == tenant_id,
                PedidoModel.es_pagado == False,
                PedidoModel.medio_pago.has(permite_cheque=True),
            )
            .all()
        )

        for pedido in pedidos_con_cheques:
            if cliente_id and pedido.cliente_id != cliente_id:
                continue
            if local_id and pedido.local_id != local_id:
                continue

            cheques_pendientes = [
                c for c in pedido.cheques if c.estado_id not in ids_estados_cobrado
            ]
            sin_cheques = len(pedido.cheques) == 0

            if sin_cheques:
                # Pedido con medio cheque pero sin cheques ingresados aún
                descuento_nc = sum(float(nc.monto) for nc in pedido.notas_credito) if pedido.notas_credito else 0.0
                monto_pendiente = float(pedido.monto_total) - descuento_nc
                fecha_venc_proxima = datetime.now(timezone.utc) + timedelta(days=30)
                dias_vencimiento = 30
                entry_estado = "SIN_CHEQUES"
            else:
                if not cheques_pendientes:
                    continue
                monto_pendiente = sum(float(c.monto) for c in cheques_pendientes)
                fecha_venc_proxima = min(c.fecha_vencimiento for c in cheques_pendientes)
                dias_vencimiento = (fecha_venc_proxima.date() - datetime.now(timezone.utc).date()).days
                entry_estado = "VENCIDO" if dias_vencimiento < 0 else "PENDIENTE"

            if estado and entry_estado != estado:
                continue

            resultado.append({
                "tipo": "CHEQUE",
                "referencia_id": pedido.id,
                "pedido_id": pedido.id,
                "numero_pedido": pedido.numero_pedido,
                "cliente_id": pedido.cliente_id,
                "cliente_nombre": pedido.cliente.nombre if pedido.cliente else None,
                "local_id": pedido.local_id,
                "local_nombre": pedido.local.nombre if pedido.local else None,
                "monto_total": float(pedido.monto_total) - descuento_nc,
                "monto_pendiente": monto_pendiente,
                "cantidad_cheques": len(cheques_pendientes) if not sin_cheques else None,
                "sin_cheques": sin_cheques,
                "fecha_vencimiento": fecha_venc_proxima.isoformat(),
                "dias_vencimiento": dias_vencimiento,
                "estado": entry_estado,
                "medio_pago_nombre": pedido.medio_pago.nombre if pedido.medio_pago else None,
                "tipo_documento": pedido.tipo_documento_tributario.nombre if pedido.tipo_documento_tributario else None,
                "fecha_creacion": pedido.fecha_pedido.isoformat() if pedido.fecha_pedido else None,
                "entregado": (pedido.despacho is not None and pedido.despacho.estado_despacho.value == "ENTREGADO") or (pedido.estado_pedido is not None and pedido.estado_pedido.es_final),
                "estado_pedido_nombre": pedido.estado_pedido.nombre if pedido.estado_pedido else None,
                "estado_pedido_color": pedido.estado_pedido.color if pedido.estado_pedido else None,
            })

    # ── 2. TRANSFERENCIAS Y OTROS DIFERIDOS ───────────────────────────────────
    if tipo in (None, "TRANSFERENCIA"):
        query = db.query(CobroPendienteModel).filter(
            CobroPendienteModel.tenant_id == tenant_id
        )
        if estado:
            query = query.filter(CobroPendienteModel.estado == estado)
        else:
            query = query.filter(CobroPendienteModel.estado.in_(["PENDIENTE", "VENCIDO"]))

        cobros = query.all()

        for cobro in cobros:
            pedido = cobro.pedido
            if not pedido:
                continue
            if cliente_id and pedido.cliente_id != cliente_id:
                continue
            if local_id and pedido.local_id != local_id:
                continue

            dias_vencimiento = (cobro.fecha_vencimiento.date() - datetime.now(timezone.utc).date()).days

            resultado.append({
                "tipo": "TRANSFERENCIA",
                "referencia_id": cobro.id,  # CobroPendiente.id (para confirmar/anular)
                "pedido_id": pedido.id,
                "numero_pedido": pedido.numero_pedido,
                "cliente_id": pedido.cliente_id,
                "cliente_nombre": pedido.cliente.nombre if pedido.cliente else None,
                "local_id": pedido.local_id,
                "local_nombre": pedido.local.nombre if pedido.local else None,
                "monto_total": float(pedido.monto_total),
                "monto_pendiente": float(cobro.monto),
                "cantidad_cheques": None,
                "fecha_vencimiento": cobro.fecha_vencimiento.isoformat(),
                "dias_vencimiento": dias_vencimiento,
                "estado": cobro.estado,
                "medio_pago_nombre": pedido.medio_pago.nombre if pedido.medio_pago else None,
                "tipo_documento": pedido.tipo_documento_tributario.nombre if pedido.tipo_documento_tributario else None,
                "fecha_creacion": cobro.fecha_creacion.isoformat() if cobro.fecha_creacion else None,
                "observaciones": cobro.observaciones,
                "entregado": (pedido.despacho is not None and pedido.despacho.estado_despacho.value == "ENTREGADO") or (pedido.estado_pedido is not None and pedido.estado_pedido.es_final),
                "estado_pedido_nombre": pedido.estado_pedido.nombre if pedido.estado_pedido else None,
                "estado_pedido_color": pedido.estado_pedido.color if pedido.estado_pedido else None,
            })

    # Ordenar por fecha_vencimiento más próxima primero
    resultado.sort(key=lambda x: x["fecha_vencimiento"])
    return resultado


@router.patch("/{cobro_id}/confirmar")
def confirmar_cobro(
    cobro_id: int,
    observaciones: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Confirma la recepción de un cobro diferido (transferencia).
    Marca el pedido como pagado y libera el crédito del cliente.
    """
    cobro = db.query(CobroPendienteModel).filter(
        CobroPendienteModel.id == cobro_id,
        CobroPendienteModel.tenant_id == current_user.tenant_id,
    ).first()
    if not cobro:
        raise HTTPException(status_code=404, detail="Cobro pendiente no encontrado")
    if cobro.estado != "PENDIENTE" and cobro.estado != "VENCIDO":
        raise HTTPException(status_code=400, detail=f"El cobro ya está en estado {cobro.estado}")

    cobro.estado = "RECIBIDO"
    cobro.fecha_recepcion = datetime.now(timezone.utc)
    if observaciones:
        cobro.observaciones = observaciones

    # Marcar pedido como pagado
    pedido = cobro.pedido
    if pedido:
        pedido.es_pagado = True
        # Liberar crédito del cliente
        if pedido.cliente_id:
            CreditoService.liberar_credito(pedido.cliente_id, float(cobro.monto), db)

    db.commit()
    return {"mensaje": "Cobro confirmado correctamente", "cobro_id": cobro_id}


@router.patch("/{cobro_id}/anular")
def anular_cobro(
    cobro_id: int,
    observaciones: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Anula un cobro diferido pendiente (ej: pedido cancelado).
    Libera el crédito del cliente sin marcar como pagado.
    """
    cobro = db.query(CobroPendienteModel).filter(
        CobroPendienteModel.id == cobro_id,
        CobroPendienteModel.tenant_id == current_user.tenant_id,
    ).first()
    if not cobro:
        raise HTTPException(status_code=404, detail="Cobro pendiente no encontrado")
    if cobro.estado not in ("PENDIENTE", "VENCIDO"):
        raise HTTPException(status_code=400, detail=f"El cobro ya está en estado {cobro.estado}")

    cobro.estado = "ANULADO"
    if observaciones:
        cobro.observaciones = observaciones

    # Liberar crédito sin marcar pedido como pagado
    pedido = cobro.pedido
    if pedido and pedido.cliente_id:
        CreditoService.liberar_credito(pedido.cliente_id, float(cobro.monto), db)

    db.commit()
    return {"mensaje": "Cobro anulado correctamente", "cobro_id": cobro_id}


@router.get("/resumen")
def resumen_cobranza(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Resumen de cobranza del tenant: totales por estado y tipo.
    """
    tenant_id = current_user.tenant_id

    # Cobros diferidos
    cobros = db.query(CobroPendienteModel).filter(
        CobroPendienteModel.tenant_id == tenant_id
    ).all()

    hoy = datetime.now(timezone.utc).date()
    vencidos_transferencia = sum(
        float(c.monto) for c in cobros
        if c.estado == "PENDIENTE" and c.fecha_vencimiento.date() < hoy
    )
    pendientes_transferencia = sum(
        float(c.monto) for c in cobros
        if c.estado == "PENDIENTE" and c.fecha_vencimiento.date() >= hoy
    )

    # Cheques pendientes
    estados_cobrado = db.query(EstadoChequeModel).filter(
        EstadoChequeModel.codigo.in_(["COBRADO", "ANULADO"])
    ).all()
    ids_estados_cobrado = {e.id for e in estados_cobrado}

    pedidos_cheque = db.query(PedidoModel).filter(
        PedidoModel.tenant_id == tenant_id,
        PedidoModel.es_pagado == False,
        PedidoModel.medio_pago.has(permite_cheque=True),
    ).all()

    monto_cheques_pendientes = 0.0
    for pedido in pedidos_cheque:
        cheques_pend = [c for c in pedido.cheques if c.estado_id not in ids_estados_cobrado]
        monto_cheques_pendientes += sum(float(c.monto) for c in cheques_pend)

    return {
        "cheques": {
            "monto_pendiente": monto_cheques_pendientes,
            "cantidad_pedidos": len(pedidos_cheque),
        },
        "transferencias": {
            "monto_pendiente": pendientes_transferencia,
            "monto_vencido": vencidos_transferencia,
            "cantidad_cobros": len([c for c in cobros if c.estado == "PENDIENTE"]),
        },
        "total_por_cobrar": monto_cheques_pendientes + pendientes_transferencia + vencidos_transferencia,
    }
