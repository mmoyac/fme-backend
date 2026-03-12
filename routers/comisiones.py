"""
Router de Comisiones de Vendedores.
GET  /api/comisiones/           → Lista de comisiones (admin: todas; vendedor: propias)
GET  /api/comisiones/periodos   → Períodos disponibles
GET  /api/comisiones/resumen    → Resumen por vendedor y período
POST /api/comisiones/liquidaciones        → Crear liquidación
GET  /api/comisiones/liquidaciones        → Listar liquidaciones
PUT  /api/comisiones/liquidaciones/{id}/pagar → Marcar como pagada
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, distinct

from database.database import get_db
from database.models import Comision, LiquidacionComision, User
from routers.auth import get_current_active_user
from schemas.comisiones import ComisionOut, LiquidacionCreate, LiquidacionOut, ResumenVendedorPeriodo
from services.comisiones_service import crear_liquidacion

router = APIRouter()


def _es_admin(user) -> bool:
    return user.role and user.role.nombre.lower() == "admin"


# ──────────────────────────────────────────────
# COMISIONES
# ──────────────────────────────────────────────

@router.get("/", response_model=List[ComisionOut], summary="Listar comisiones")
def listar_comisiones(
    periodo: Optional[str] = Query(None, description="Filtrar por período YYYY-MM"),
    vendedor_id: Optional[int] = Query(None, description="Filtrar por vendedor (solo admin)"),
    estado: Optional[str] = Query(None, description="PENDIENTE o LIQUIDADA"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = (
        db.query(Comision)
        .options(joinedload(Comision.vendedor))
        .filter(Comision.tenant_id == current_user.tenant_id)
    )

    # Vendedor solo ve sus propias comisiones
    if not _es_admin(current_user):
        q = q.filter(Comision.vendedor_id == current_user.id)
    elif vendedor_id:
        q = q.filter(Comision.vendedor_id == vendedor_id)

    if periodo:
        q = q.filter(Comision.periodo == periodo)
    if estado:
        q = q.filter(Comision.estado == estado.upper())

    comisiones = q.order_by(Comision.fecha_generacion.desc()).offset(skip).limit(limit).all()

    _skip = {"monto_bruto", "monto_neto", "monto_comision", "porcentaje"}
    return [
        ComisionOut(
            **{k: v for k, v in comision.__dict__.items() if not k.startswith("_") and k not in _skip},
            vendedor_nombre=comision.vendedor.nombre_completo if comision.vendedor else None,
            monto_bruto=float(comision.monto_bruto),
            monto_neto=float(comision.monto_neto),
            monto_comision=float(comision.monto_comision),
            porcentaje=float(comision.porcentaje),
        )
        for comision in comisiones
    ]


@router.get("/periodos", summary="Períodos con comisiones disponibles")
def listar_periodos(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = db.query(distinct(Comision.periodo)).filter(Comision.tenant_id == current_user.tenant_id)
    if not _es_admin(current_user):
        q = q.filter(Comision.vendedor_id == current_user.id)
    periodos = [row[0] for row in q.order_by(Comision.periodo.desc()).all()]
    return {"periodos": periodos}


@router.get("/resumen", response_model=List[ResumenVendedorPeriodo], summary="Resumen por vendedor y período")
def resumen_comisiones(
    periodo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Solo admin puede ver el resumen de todos los vendedores."""
    if not _es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver el resumen global")

    q = (
        db.query(
            Comision.vendedor_id,
            Comision.periodo,
            func.sum(Comision.monto_neto).label("total_neto"),
            func.sum(Comision.monto_comision).label("total_comision"),
            func.count(Comision.id).label("cantidad"),
        )
        .filter(Comision.tenant_id == current_user.tenant_id)
    )
    if periodo:
        q = q.filter(Comision.periodo == periodo)

    rows = q.group_by(Comision.vendedor_id, Comision.periodo).all()

    # IDs de liquidaciones existentes por vendedor+periodo
    liquidaciones = {
        (liq.vendedor_id, liq.periodo)
        for liq in db.query(LiquidacionComision.vendedor_id, LiquidacionComision.periodo)
        .filter(LiquidacionComision.tenant_id == current_user.tenant_id)
        .all()
    }

    # Cargar nombres de vendedores
    user_ids = list({r.vendedor_id for r in rows})
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}

    return [
        ResumenVendedorPeriodo(
            vendedor_id=row.vendedor_id,
            vendedor_nombre=users.get(row.vendedor_id, type("u", (), {"nombre_completo": None})).nombre_completo,
            porcentaje_comision=float(users[row.vendedor_id].porcentaje_comision)
            if row.vendedor_id in users and users[row.vendedor_id].porcentaje_comision
            else None,
            periodo=row.periodo,
            total_ventas_neto=round(float(row.total_neto), 2),
            total_comision=round(float(row.total_comision), 2),
            cantidad_pedidos=row.cantidad,
            tiene_liquidacion=(row.vendedor_id, row.periodo) in liquidaciones,
        )
        for row in rows
    ]


# ──────────────────────────────────────────────
# LIQUIDACIONES
# ──────────────────────────────────────────────

@router.get("/liquidaciones", response_model=List[LiquidacionOut], summary="Listar liquidaciones")
def listar_liquidaciones(
    vendedor_id: Optional[int] = Query(None),
    periodo: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    q = (
        db.query(LiquidacionComision)
        .options(joinedload(LiquidacionComision.vendedor))
        .filter(LiquidacionComision.tenant_id == current_user.tenant_id)
    )

    if not _es_admin(current_user):
        q = q.filter(LiquidacionComision.vendedor_id == current_user.id)
    elif vendedor_id:
        q = q.filter(LiquidacionComision.vendedor_id == vendedor_id)

    if periodo:
        q = q.filter(LiquidacionComision.periodo == periodo)
    if estado:
        q = q.filter(LiquidacionComision.estado == estado.upper())

    liquidaciones = q.order_by(LiquidacionComision.periodo.desc()).all()

    _liq_skip = {"total_ventas_neto", "total_comision"}
    return [
        LiquidacionOut(
            **{k: v for k, v in liq.__dict__.items() if not k.startswith("_") and k not in _liq_skip},
            vendedor_nombre=liq.vendedor.nombre_completo if liq.vendedor else None,
            total_ventas_neto=float(liq.total_ventas_neto),
            total_comision=float(liq.total_comision),
        )
        for liq in liquidaciones
    ]


@router.post("/liquidaciones", response_model=LiquidacionOut, status_code=status.HTTP_201_CREATED, summary="Crear liquidación")
def crear_nueva_liquidacion(
    data: LiquidacionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Solo admin puede crear liquidaciones."""
    if not _es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear liquidaciones")

    # Validar vendedor pertenece al tenant
    vendedor = db.query(User).filter(
        User.id == data.vendedor_id,
        User.tenant_id == current_user.tenant_id,
    ).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    try:
        liq = crear_liquidacion(
            vendedor_id=data.vendedor_id,
            periodo=data.periodo,
            tenant_id=current_user.tenant_id,
            notas=data.notas or "",
            db=db,
        )
        db.commit()
        db.refresh(liq)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _liq_skip = {"total_ventas_neto", "total_comision"}
    return LiquidacionOut(
        **{k: v for k, v in liq.__dict__.items() if not k.startswith("_") and k not in _liq_skip},
        vendedor_nombre=vendedor.nombre_completo,
        total_ventas_neto=float(liq.total_ventas_neto),
        total_comision=float(liq.total_comision),
    )


@router.put("/liquidaciones/{liquidacion_id}/pagar", response_model=LiquidacionOut, summary="Marcar liquidación como pagada")
def marcar_pagada(
    liquidacion_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Solo admin puede marcar como pagada."""
    if not _es_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden registrar pagos")

    liq = db.query(LiquidacionComision).filter(
        LiquidacionComision.id == liquidacion_id,
        LiquidacionComision.tenant_id == current_user.tenant_id,
    ).first()
    if not liq:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    if liq.estado == "PAGADA":
        raise HTTPException(status_code=400, detail="La liquidación ya está marcada como pagada")

    try:
        from zoneinfo import ZoneInfo
        liq.fecha_pago_real = datetime.now(ZoneInfo("America/Santiago"))
    except Exception:
        liq.fecha_pago_real = datetime.utcnow()

    liq.estado = "PAGADA"
    db.commit()
    db.refresh(liq)

    vendedor = db.query(User).filter(User.id == liq.vendedor_id).first()
    _liq_skip = {"total_ventas_neto", "total_comision"}
    return LiquidacionOut(
        **{k: v for k, v in liq.__dict__.items() if not k.startswith("_") and k not in _liq_skip},
        vendedor_nombre=vendedor.nombre_completo if vendedor else None,
        total_ventas_neto=float(liq.total_ventas_neto),
        total_comision=float(liq.total_comision),
    )
