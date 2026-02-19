"""
Router para gestión de cheques asociados a pedidos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database.database import get_db
from database.models import Cheque as ChequeModel, Pedido as PedidoModel, EstadoCheque as EstadoChequeModel, MedioPago as MedioPagoModel
from database.models import User
from schemas.cheque import (
    Cheque, ChequeCreate, ChequeUpdate, ChequeConEstado,
    ResumenChequesPedido, PedidoConCheques
)
from routers.auth import get_current_active_user
from services.credito_service import CreditoService

router = APIRouter()


# Dependencia para verificar que el usuario es admin
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role.nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user


def calcular_estado_pago_pedido(pedido: PedidoModel, db: Session) -> bool:
    """
    Calcula si un pedido debe marcarse como pagado basado en el estado de sus cheques.
    
    Reglas:
    - Si medio de pago no permite cheques: usar lógica actual (MP, efectivo, etc)
    - Si medio de pago es CHEQUE: todos los cheques deben estar COBRADOS
    """
    if not pedido.medio_pago:
        return pedido.es_pagado  # Mantener estado actual si no hay medio definido
    
    if not pedido.medio_pago.permite_cheque:
        return pedido.es_pagado  # Para otros medios, mantener lógica actual
    
    # Para pagos con cheque, verificar que todos estén cobrados
    if not pedido.cheques:
        return False  # Si el pago es con cheques pero no hay cheques registrados
    
    estado_cobrado = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "COBRADO").first()
    if not estado_cobrado:
        return False
    
    cheques_cobrados = len([c for c in pedido.cheques if c.estado_id == estado_cobrado.id])
    return cheques_cobrados == len(pedido.cheques)


@router.get("/pedido/{pedido_id}", response_model=PedidoConCheques)
def obtener_pedido_con_cheques(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener pedido con información detallada de cheques."""
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Calcular resumen de cheques si existen
    resumen_cheques = None
    if pedido.cheques:
        estado_cobrado = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "COBRADO").first()
        estado_rechazado = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "RECHAZADO").first()
        
        total_cheques = len(pedido.cheques)
        monto_total = sum(c.monto for c in pedido.cheques)
        cheques_cobrados = len([c for c in pedido.cheques if c.estado_id == estado_cobrado.id]) if estado_cobrado else 0
        cheques_rechazados = len([c for c in pedido.cheques if c.estado_id == estado_rechazado.id]) if estado_rechazado else 0
        cheques_pendientes = total_cheques - cheques_cobrados - cheques_rechazados
        
        resumen_cheques = ResumenChequesPedido(
            total_cheques=total_cheques,
            monto_total_cheques=monto_total,
            cheques_pendientes=cheques_pendientes,
            cheques_cobrados=cheques_cobrados,
            cheques_rechazados=cheques_rechazados,
            todos_cobrados=(cheques_cobrados == total_cheques and total_cheques > 0)
        )
    
    return PedidoConCheques(
        pedido_id=pedido.id,
        numero_pedido=pedido.numero_pedido,
        monto_total=pedido.monto_total,
        es_pagado=pedido.es_pagado,
        medio_pago_codigo=pedido.medio_pago.codigo if pedido.medio_pago else None,
        resumen_cheques=resumen_cheques,
        cheques=[ChequeConEstado.model_validate(c) for c in pedido.cheques]
    )


@router.post("/", response_model=Cheque)
def crear_cheque(
    cheque: ChequeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo cheque asociado a un pedido."""
    # Verificar que el pedido existe
    pedido = db.query(PedidoModel).filter(PedidoModel.id == cheque.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Si no se especifica estado, usar PENDIENTE por defecto
    if not cheque.estado_id:
        estado_pendiente = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "PENDIENTE").first()
        if not estado_pendiente:
            raise HTTPException(status_code=400, detail="Estado PENDIENTE no encontrado")
        cheque.estado_id = estado_pendiente.id
    
    # Crear el cheque
    db_cheque = ChequeModel(**cheque.model_dump())
    db.add(db_cheque)
    db.commit()
    db.refresh(db_cheque)
    
    # Recalcular estado de pago del pedido
    pedido.es_pagado = calcular_estado_pago_pedido(pedido, db)
    db.commit()
    
    return db_cheque


@router.put("/{cheque_id}", response_model=Cheque)
def actualizar_cheque(
    cheque_id: int,
    cheque_update: ChequeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar estado de un cheque y recalcular estado de pago del pedido."""
    db_cheque = db.query(ChequeModel).filter(ChequeModel.id == cheque_id).first()
    if not db_cheque:
        raise HTTPException(status_code=404, detail="Cheque no encontrado")
    
    # Actualizar campos
    update_data = cheque_update.model_dump(exclude_unset=True)
    
    # Guardar estado anterior para detectar cambios
    estado_anterior = None
    if db_cheque.estado_id:
        estado_anterior = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == db_cheque.estado_id).first()
    
    for field, value in update_data.items():
        setattr(db_cheque, field, value)
    
    # Si se cambia a estado DEPOSITADO y no tenía fecha de depósito, ponerla
    if cheque_update.estado_id:
        estado_nuevo = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == cheque_update.estado_id).first()
        if estado_nuevo and estado_nuevo.codigo == "DEPOSITADO" and not db_cheque.fecha_deposito:
            db_cheque.fecha_deposito = datetime.now()
        elif estado_nuevo and estado_nuevo.codigo == "COBRADO" and not db_cheque.fecha_cobro:
            db_cheque.fecha_cobro = datetime.now()
    
    db.commit()
    db.refresh(db_cheque)
    
    # Liberar crédito si el cheque cambia a COBRADO
    if cheque_update.estado_id:
        estado_nuevo = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == cheque_update.estado_id).first()
        if (estado_nuevo and estado_nuevo.codigo == "COBRADO" and 
            (not estado_anterior or estado_anterior.codigo != "COBRADO")):
            try:
                # Obtener el pedido para obtener el cliente_id
                pedido = db.query(PedidoModel).filter(PedidoModel.id == db_cheque.pedido_id).first()
                if pedido:
                    success = CreditoService.liberar_credito(pedido.cliente_id, float(db_cheque.monto), db)
                    if success:
                        print(f"✅ Crédito liberado: ${db_cheque.monto} para cliente {pedido.cliente_id}")
                    else:
                        print(f"⚠️  No se pudo liberar crédito para cliente {pedido.cliente_id}")
            except Exception as e:
                print(f"⚠️  Error al liberar crédito: {e}")
                # No fallar la actualización del cheque por error de crédito
    
    # Recalcular estado de pago del pedido asociado
    pedido = db.query(PedidoModel).filter(PedidoModel.id == db_cheque.pedido_id).first()
    if pedido:
        pedido.es_pagado = calcular_estado_pago_pedido(pedido, db)
        db.commit()
    
    return db_cheque


@router.delete("/{cheque_id}")
def eliminar_cheque(
    cheque_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un cheque y recalcular estado de pago del pedido."""
    db_cheque = db.query(ChequeModel).filter(ChequeModel.id == cheque_id).first()
    if not db_cheque:
        raise HTTPException(status_code=404, detail="Cheque no encontrado")
    
    pedido_id = db_cheque.pedido_id
    
    db.delete(db_cheque)
    db.commit()
    
    # Recalcular estado de pago del pedido
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if pedido:
        pedido.es_pagado = calcular_estado_pago_pedido(pedido, db)
        db.commit()
    
    return {"message": "Cheque eliminado exitosamente"}


@router.get("/pedido/{pedido_id}/resumen", response_model=ResumenChequesPedido)
def obtener_resumen_cheques_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener resumen de cheques de un pedido."""
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    if not pedido.cheques:
        raise HTTPException(status_code=404, detail="El pedido no tiene cheques asociados")
    
    estado_cobrado = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "COBRADO").first()
    estado_rechazado = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == "RECHAZADO").first()
    
    total_cheques = len(pedido.cheques)
    monto_total = sum(c.monto for c in pedido.cheques)
    cheques_cobrados = len([c for c in pedido.cheques if c.estado_id == estado_cobrado.id]) if estado_cobrado else 0
    cheques_rechazados = len([c for c in pedido.cheques if c.estado_id == estado_rechazado.id]) if estado_rechazado else 0
    cheques_pendientes = total_cheques - cheques_cobrados - cheques_rechazados
    
    return ResumenChequesPedido(
        total_cheques=total_cheques,
        monto_total_cheques=monto_total,
        cheques_pendientes=cheques_pendientes,
        cheques_cobrados=cheques_cobrados,
        cheques_rechazados=cheques_rechazados,
        todos_cobrados=(cheques_cobrados == total_cheques and total_cheques > 0)
    )