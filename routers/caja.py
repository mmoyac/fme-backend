"""
Router para endpoints de Caja y Turnos.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, date
from decimal import Decimal

from database.database import get_db
from database.models import TurnoCaja, OperacionCaja, User, Local, MedioPago, Pedido, EstadoTurnoCaja, TipoOperacionCaja
from schemas.caja import (
    TurnoCajaCreate,
    TurnoCajaClose,
    TurnoCajaResponse,
    TurnoCajaConOperaciones,
    OperacionCajaCreate,
    OperacionCajaResponse,
    EstadoCajaVendedor,
    ResumenCajaLocal,
    ReporteCajaDiario
)
from routers.auth import get_current_active_user
from utils.pdf_reports import generar_pdf_cierre_caja

router = APIRouter()


def calcular_efectivo_esperado(turno: TurnoCaja, db: Session) -> Decimal:
    """Calcula el efectivo esperado en caja basado en las operaciones."""
    total_operaciones = db.query(func.sum(OperacionCaja.monto)).filter(
        and_(
            OperacionCaja.turno_caja_id == turno.id,
            or_(
                OperacionCaja.tipo_operacion == TipoOperacionCaja.APERTURA,
                OperacionCaja.tipo_operacion == TipoOperacionCaja.VENTA,
                OperacionCaja.tipo_operacion == TipoOperacionCaja.INGRESO
            )
        )
    ).scalar() or Decimal('0.00')
    
    total_egresos = db.query(func.sum(OperacionCaja.monto)).filter(
        and_(
            OperacionCaja.turno_caja_id == turno.id,
            or_(
                OperacionCaja.tipo_operacion == TipoOperacionCaja.EGRESO,
                OperacionCaja.tipo_operacion == TipoOperacionCaja.DEVOLUCION
            )
        )
    ).scalar() or Decimal('0.00')
    
    return total_operaciones - total_egresos


# ============================================
# GESTIÓN DE TURNOS DE CAJA
# ============================================

@router.get("/local/{local_id}/caja-abierta")
def verificar_caja_abierta(
    local_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifica si hay alguna caja abierta en el local especificado.
    
    **Retorna:**
    - `tiene_caja_abierta`: boolean
    - `turno`: información del turno abierto (si existe)
    """
    # Verificar que el local exista y pertenezca al tenant
    local = db.query(Local).filter(Local.id == local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Buscar turno abierto en el local
    turno_abierto = db.query(TurnoCaja).filter(
        and_(
            TurnoCaja.local_id == local_id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    if turno_abierto:
        vendedor = db.query(User).filter(User.id == turno_abierto.vendedor_id).first()
        return {
            "tiene_caja_abierta": True,
            "turno": {
                "id": turno_abierto.id,
                "vendedor_nombre": vendedor.nombre_completo if vendedor else "Desconocido",
                "fecha_apertura": turno_abierto.fecha_apertura,
                "monto_inicial": float(turno_abierto.monto_inicial)
            },
            "local_nombre": local.nombre
        }
    
    return {
        "tiene_caja_abierta": False,
        "turno": None,
        "local_nombre": local.nombre,
        "mensaje": f"No hay caja abierta en '{local.nombre}'. Se debe abrir un turno antes de confirmar pedidos."
    }

@router.post("/turno/abrir", response_model=TurnoCajaResponse, status_code=status.HTTP_201_CREATED)
def abrir_caja(
    turno_data: TurnoCajaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Abrir un nuevo turno de caja para el vendedor actual.
    
    **Validaciones:**
    - El vendedor no debe tener otro turno abierto
    - El local debe existir y estar activo
    """
    # Verificar que el vendedor no tenga un turno abierto
    turno_abierto = db.query(TurnoCaja).filter(
        and_(
            TurnoCaja.vendedor_id == current_user.id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    if turno_abierto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya tienes un turno de caja abierto (ID: {turno_abierto.id})"
        )
    
    # Verificar que el vendedor solo pueda trabajar en su local asignado (si tiene uno)
    if current_user.local_defecto_id is not None:
        if turno_data.local_id != current_user.local_defecto_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para abrir caja en este local. Tu local asignado es: {current_user.local_defecto_id}"
            )
    
    # Verificar que el local exista y pertenezca al tenant
    local = db.query(Local).filter(Local.id == turno_data.local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {turno_data.local_id} no encontrado"
        )
    
    # Verificar que no sea el local WEB (Tienda Online no tiene caja física)
    if local.codigo == 'WEB':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede abrir caja en el local de Tienda Online (WEB). Solo locales físicos requieren caja."
        )
    
    # Crear nuevo turno
    turno = TurnoCaja(
        vendedor_id=current_user.id,
        local_id=turno_data.local_id,
        monto_inicial=turno_data.monto_inicial,
        observaciones_apertura=turno_data.observaciones_apertura,
        estado=EstadoTurnoCaja.ABIERTO
    )
    db.add(turno)
    db.flush()
    
    # Registrar operación de apertura
    if turno_data.monto_inicial > 0:
        operacion_apertura = OperacionCaja(
            turno_caja_id=turno.id,
            tipo_operacion=TipoOperacionCaja.APERTURA,
            monto=turno_data.monto_inicial,
            descripcion="Apertura de caja",
            observaciones=turno_data.observaciones_apertura
        )
        db.add(operacion_apertura)
    
    db.commit()
    db.refresh(turno)
    
    return TurnoCajaResponse(
        id=turno.id,
        vendedor_id=turno.vendedor_id,
        local_id=turno.local_id,
        fecha_apertura=turno.fecha_apertura,
        estado=turno.estado,
        monto_inicial=turno.monto_inicial,
        observaciones_apertura=turno.observaciones_apertura,
        vendedor_nombre=current_user.nombre_completo,
        vendedor_email=current_user.email,
        local_nombre=local.nombre
    )


@router.put("/turno/{turno_id}/cerrar", response_model=TurnoCajaResponse)
def cerrar_caja(
    turno_id: int,
    cierre_data: TurnoCajaClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cerrar un turno de caja específico.
    
    **Validaciones:**
    - El turno debe pertenecer al vendedor actual
    - El turno debe estar abierto
    """
    turno = db.query(TurnoCaja).filter(
        and_(
            TurnoCaja.id == turno_id,
            TurnoCaja.vendedor_id == current_user.id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno de caja no encontrado o ya cerrado"
        )
    
    # Calcular efectivo esperado
    efectivo_esperado = calcular_efectivo_esperado(turno, db)
    diferencia = cierre_data.efectivo_real - efectivo_esperado
    
    # Actualizar turno
    turno.fecha_cierre = datetime.now()
    turno.estado = EstadoTurnoCaja.CERRADO
    turno.efectivo_esperado = efectivo_esperado
    turno.efectivo_real = cierre_data.efectivo_real
    turno.diferencia = diferencia
    turno.observaciones_cierre = cierre_data.observaciones_cierre
    
    # Registrar operación de cierre
    operacion_cierre = OperacionCaja(
        turno_caja_id=turno.id,
        tipo_operacion=TipoOperacionCaja.CIERRE,
        monto=cierre_data.efectivo_real,
        descripcion=f"Cierre de caja - Diferencia: ${diferencia}",
        observaciones=cierre_data.observaciones_cierre
    )
    db.add(operacion_cierre)
    
    db.commit()
    db.refresh(turno)
    
    return TurnoCajaResponse(
        id=turno.id,
        vendedor_id=turno.vendedor_id,
        local_id=turno.local_id,
        fecha_apertura=turno.fecha_apertura,
        fecha_cierre=turno.fecha_cierre,
        estado=turno.estado,
        monto_inicial=turno.monto_inicial,
        efectivo_esperado=turno.efectivo_esperado,
        efectivo_real=turno.efectivo_real,
        diferencia=turno.diferencia,
        observaciones_apertura=turno.observaciones_apertura,
        observaciones_cierre=turno.observaciones_cierre,
        vendedor_nombre=current_user.nombre_completo,
        vendedor_email=current_user.email,
        local_nombre=turno.local.nombre
    )


@router.get("/turno/actual", response_model=TurnoCajaResponse)
def obtener_turno_actual(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener el turno de caja actualmente abierto del vendedor.
    """
    turno = db.query(TurnoCaja).options(
        joinedload(TurnoCaja.local),
        joinedload(TurnoCaja.vendedor)
    ).filter(
        and_(
            TurnoCaja.vendedor_id == current_user.id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes un turno de caja abierto"
        )
    
    # Calcular efectivo esperado actual
    efectivo_esperado = calcular_efectivo_esperado(turno, db)
    
    return TurnoCajaResponse(
        id=turno.id,
        vendedor_id=turno.vendedor_id,
        local_id=turno.local_id,
        fecha_apertura=turno.fecha_apertura,
        estado=turno.estado,
        monto_inicial=turno.monto_inicial,
        efectivo_esperado=efectivo_esperado,
        observaciones_apertura=turno.observaciones_apertura,
        vendedor_nombre=turno.vendedor.nombre_completo,
        vendedor_email=turno.vendedor.email,
        local_nombre=turno.local.nombre
    )


@router.get("/turno/{turno_id}", response_model=TurnoCajaConOperaciones)
def obtener_turno_detalle(
    turno_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener detalle completo de un turno específico con todas sus operaciones.
    """
    turno = db.query(TurnoCaja).options(
        joinedload(TurnoCaja.local),
        joinedload(TurnoCaja.vendedor),
        joinedload(TurnoCaja.operaciones)
    ).join(Local).filter(
        and_(
            TurnoCaja.id == turno_id,
            TurnoCaja.vendedor_id == current_user.id,
            Local.tenant_id == current_user.tenant_id
        )
    ).first()
    
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno de caja no encontrado"
        )
    
    # Mapear operaciones
    operaciones = []
    for op in turno.operaciones:
        operaciones.append(OperacionCajaResponse(
            id=op.id,
            turno_caja_id=op.turno_caja_id,
            tipo_operacion=op.tipo_operacion,
            fecha_operacion=op.fecha_operacion,
            monto=op.monto,
            descripcion=op.descripcion,
            observaciones=op.observaciones,
            pedido_id=op.pedido_id,
            medio_pago_id=op.medio_pago_id,
            medio_pago_codigo=op.medio_pago.codigo if op.medio_pago else None,
            medio_pago_nombre=op.medio_pago.nombre if op.medio_pago else None
        ))
    
    return TurnoCajaConOperaciones(
        id=turno.id,
        vendedor_id=turno.vendedor_id,
        local_id=turno.local_id,
        fecha_apertura=turno.fecha_apertura,
        fecha_cierre=turno.fecha_cierre,
        estado=turno.estado,
        monto_inicial=turno.monto_inicial,
        efectivo_esperado=turno.efectivo_esperado,
        efectivo_real=turno.efectivo_real,
        diferencia=turno.diferencia,
        observaciones_apertura=turno.observaciones_apertura,
        observaciones_cierre=turno.observaciones_cierre,
        vendedor_nombre=turno.vendedor.nombre_completo,
        vendedor_email=turno.vendedor.email,
        local_nombre=turno.local.nombre,
        operaciones=operaciones
    )


# ============================================
# GESTIÓN DE OPERACIONES DE CAJA
# ============================================

@router.post("/operacion", response_model=OperacionCajaResponse, status_code=status.HTTP_201_CREATED)
def registrar_operacion(
    operacion_data: OperacionCajaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Registrar una operación manual de caja (ingreso o egreso).
    
    **Validaciones:**
    - El vendedor debe tener un turno abierto
    - El tipo de operación debe ser INGRESO o EGRESO
    """
    # Buscar turno activo
    turno = db.query(TurnoCaja).filter(
        and_(
            TurnoCaja.vendedor_id == current_user.id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes un turno de caja abierto"
        )
    
    # Validar tipo de operación
    if operacion_data.tipo_operacion not in [TipoOperacionCaja.INGRESO, TipoOperacionCaja.EGRESO, TipoOperacionCaja.DEVOLUCION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten operaciones tipo INGRESO, EGRESO o DEVOLUCION"
        )
    
    # Validar medio de pago si se especifica
    medio_pago = None
    if operacion_data.medio_pago_id:
        medio_pago = db.query(MedioPago).filter(MedioPago.id == operacion_data.medio_pago_id).first()
        if not medio_pago:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medio de pago con ID {operacion_data.medio_pago_id} no encontrado"
            )
    
    # Crear operación
    operacion = OperacionCaja(
        turno_caja_id=turno.id,
        tipo_operacion=operacion_data.tipo_operacion,
        monto=operacion_data.monto,
        descripcion=operacion_data.descripcion,
        observaciones=operacion_data.observaciones,
        medio_pago_id=operacion_data.medio_pago_id
    )
    db.add(operacion)
    db.commit()
    db.refresh(operacion)
    
    return OperacionCajaResponse(
        id=operacion.id,
        turno_caja_id=operacion.turno_caja_id,
        tipo_operacion=operacion.tipo_operacion,
        fecha_operacion=operacion.fecha_operacion,
        monto=operacion.monto,
        descripcion=operacion.descripcion,
        observaciones=operacion.observaciones,
        pedido_id=operacion.pedido_id,
        medio_pago_id=operacion.medio_pago_id,
        medio_pago_codigo=medio_pago.codigo if medio_pago else None,
        medio_pago_nombre=medio_pago.nombre if medio_pago else None
    )


# ============================================
# REPORTES Y CONSULTAS
# ============================================

@router.get("/estado", response_model=EstadoCajaVendedor)
def obtener_estado_caja(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener el estado actual de caja del vendedor con totales.
    """
    # Buscar turno activo
    turno_activo = db.query(TurnoCaja).filter(
        and_(
            TurnoCaja.vendedor_id == current_user.id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
        )
    ).first()
    
    estado = EstadoCajaVendedor(
        vendedor_id=current_user.id,
        vendedor_nombre=current_user.nombre_completo,
        tiene_caja_abierta=turno_activo is not None
    )
    
    if turno_activo:
        # Calcular totales
        total_ventas = db.query(func.sum(OperacionCaja.monto)).filter(
            and_(
                OperacionCaja.turno_caja_id == turno_activo.id,
                OperacionCaja.tipo_operacion == TipoOperacionCaja.VENTA
            )
        ).scalar() or Decimal('0.00')
        
        total_ingresos = db.query(func.sum(OperacionCaja.monto)).filter(
            and_(
                OperacionCaja.turno_caja_id == turno_activo.id,
                OperacionCaja.tipo_operacion == TipoOperacionCaja.INGRESO
            )
        ).scalar() or Decimal('0.00')
        
        total_egresos = db.query(func.sum(OperacionCaja.monto)).filter(
            and_(
                OperacionCaja.turno_caja_id == turno_activo.id,
                or_(
                    OperacionCaja.tipo_operacion == TipoOperacionCaja.EGRESO,
                    OperacionCaja.tipo_operacion == TipoOperacionCaja.DEVOLUCION
                )
            )
        ).scalar() or Decimal('0.00')
        
        efectivo_esperado = calcular_efectivo_esperado(turno_activo, db)
        
        estado.turno_activo = TurnoCajaResponse(
            id=turno_activo.id,
            vendedor_id=turno_activo.vendedor_id,
            local_id=turno_activo.local_id,
            fecha_apertura=turno_activo.fecha_apertura,
            estado=turno_activo.estado,
            monto_inicial=turno_activo.monto_inicial,
            efectivo_esperado=efectivo_esperado,
            observaciones_apertura=turno_activo.observaciones_apertura,
            vendedor_nombre=current_user.nombre_completo,
            vendedor_email=current_user.email,
            local_nombre=turno_activo.local.nombre if turno_activo.local else None
        )
        
        estado.total_ventas = total_ventas
        estado.total_ingresos = total_ingresos
        estado.total_egresos = total_egresos
        estado.efectivo_esperado = efectivo_esperado
    
    return estado


@router.get("/turnos/historial", response_model=List[TurnoCajaResponse])
def obtener_historial_turnos(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener historial de turnos del vendedor con filtros opcionales.
    """
    query = db.query(TurnoCaja).options(
        joinedload(TurnoCaja.local)
    ).join(Local).filter(
        TurnoCaja.vendedor_id == current_user.id,
        Local.tenant_id == current_user.tenant_id
    )
    
    if fecha_desde:
        query = query.filter(TurnoCaja.fecha_apertura >= fecha_desde)
    if fecha_hasta:
        query = query.filter(TurnoCaja.fecha_apertura <= fecha_hasta)
    
    turnos = query.order_by(TurnoCaja.fecha_apertura.desc()).offset(skip).limit(limit).all()
    
    resultado = []
    for turno in turnos:
        resultado.append(TurnoCajaResponse(
            id=turno.id,
            vendedor_id=turno.vendedor_id,
            local_id=turno.local_id,
            fecha_apertura=turno.fecha_apertura,
            fecha_cierre=turno.fecha_cierre,
            estado=turno.estado,
            monto_inicial=turno.monto_inicial,
            efectivo_esperado=turno.efectivo_esperado,
            efectivo_real=turno.efectivo_real,
            diferencia=turno.diferencia,
            observaciones_apertura=turno.observaciones_apertura,
            observaciones_cierre=turno.observaciones_cierre,
            vendedor_nombre=current_user.nombre_completo,
            vendedor_email=current_user.email,
            local_nombre=turno.local.nombre
        ))
    
    return resultado


@router.get("/turno/{turno_id}/pdf")
def descargar_pdf_cierre_turno(
    turno_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera y descarga un PDF con el reporte de cierre del turno especificado.
    
    Solo permite descargar PDFs de turnos del propio usuario, excepto para administradores.
    """
    # Obtener el turno con sus relaciones
    turno = db.query(TurnoCaja).options(
        joinedload(TurnoCaja.vendedor),
        joinedload(TurnoCaja.local),
        joinedload(TurnoCaja.operaciones).joinedload(OperacionCaja.medio_pago)
    ).filter(TurnoCaja.id == turno_id).first()
    
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # Validar que el usuario puede acceder a este turno
    # Solo el propio vendedor o un admin pueden generar el PDF
    if turno.vendedor_id != current_user.id and (not current_user.role or current_user.role.nombre != "admin"):
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para descargar este reporte"
        )
    
    # Validar que el turno esté cerrado
    if turno.estado != EstadoTurnoCaja.CERRADO:
        raise HTTPException(
            status_code=400, 
            detail="Solo se pueden generar PDFs de turnos cerrados"
        )
    
    # Preparar datos del turno para el PDF
    turno_data = {
        'id': turno.id,
        'local_nombre': turno.local.nombre if turno.local else 'N/A',
        'vendedor_nombre': turno.vendedor.nombre_completo if turno.vendedor else 'N/A',
        'fecha_apertura': turno.fecha_apertura.isoformat(),
        'fecha_cierre': turno.fecha_cierre.isoformat() if turno.fecha_cierre else '',
        'estado': turno.estado.value,
        'monto_inicial': turno.monto_inicial or 0,
        'efectivo_esperado': turno.efectivo_esperado or 0,
        'efectivo_real': turno.efectivo_real or 0,
        'diferencia': turno.diferencia or 0,
        'observaciones_apertura': turno.observaciones_apertura or '',
        'observaciones_cierre': turno.observaciones_cierre or ''
    }
    
    # Preparar datos de operaciones para el PDF
    operaciones_data = []
    for op in turno.operaciones:
        operaciones_data.append({
            'fecha_operacion': op.fecha_operacion.isoformat(),
            'tipo_operacion': op.tipo_operacion.value,
            'descripcion': op.descripcion or '',
            'monto': float(op.monto or 0),
            'medio_pago_nombre': op.medio_pago.nombre if op.medio_pago else None,
            'observaciones': op.observaciones or ''
        })
    
    # Generar PDF
    try:
        pdf_buffer = generar_pdf_cierre_caja(turno_data, operaciones_data)
        pdf_content = pdf_buffer.read()
        
        # Nombre del archivo
        fecha_turno = turno.fecha_cierre.strftime("%Y%m%d_%H%M") if turno.fecha_cierre else "sin_fecha"
        filename = f"cierre_caja_turno_{turno.id}_{fecha_turno}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el PDF: {str(e)}"
        )