"""
Router para gestionar puntos de clientes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from database.database import get_db
from services.puntos_service import PuntosService
from schemas.puntos_schemas import (
    PuntosClienteResponse,
    MovimientoPuntosResponse,
    UsarPuntosRequest,
    UsarPuntosResponse,
    EstadisticasPuntosResponse,
    ValidacionPuntosRequest,
    ValidacionPuntosResponse,
    EstimacionPuntosRequest,
    EstimacionPuntosResponse
)
from routers.auth import get_current_active_user
from database.models import User

router = APIRouter(
    prefix="/api/puntos",
    tags=["Puntos"],
    dependencies=[Depends(get_current_active_user)]  # Proteger todas las rutas
)


@router.get("/cliente/{cliente_id}", response_model=PuntosClienteResponse)
def obtener_puntos_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los puntos de un cliente específico.
    """
    try:
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente_id)
        return puntos_cliente
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener puntos del cliente: {str(e)}"
        )


@router.get("/cliente/{cliente_id}/historial", response_model=List[MovimientoPuntosResponse])
def obtener_historial_puntos_cliente(
    cliente_id: int,
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de movimientos de puntos de un cliente.
    """
    try:
        historial = PuntosService.obtener_historial_puntos(db, cliente_id, limite, offset)
        return historial
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de puntos: {str(e)}"
        )


@router.post("/validar", response_model=ValidacionPuntosResponse)
def validar_uso_puntos(
    validacion: ValidacionPuntosRequest,
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Valida si un cliente puede usar la cantidad de puntos solicitada.
    """
    try:
        # Obtener puntos del cliente
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente_id)
        
        # Validar uso de puntos
        valido, mensaje, descuento = PuntosService.validar_uso_puntos_en_total(
            puntos_cliente.puntos_disponibles,
            validacion.puntos_usar,
            validacion.total_pedido
        )
        
        response = ValidacionPuntosResponse(
            valido=valido,
            mensaje=mensaje,
            descuento_aplicable=descuento
        )
        
        if not valido and descuento > 0:
            # Calcular puntos máximos usables
            valor_punto = Decimal('10')
            puntos_maximos = int(validacion.total_pedido / valor_punto)
            if puntos_maximos > puntos_cliente.puntos_disponibles:
                puntos_maximos = puntos_cliente.puntos_disponibles
            response.puntos_maximos_usables = puntos_maximos
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al validar puntos: {str(e)}"
        )


@router.get("/estadisticas", response_model=EstadisticasPuntosResponse)
def obtener_estadisticas_puntos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas generales del sistema de puntos.
    """
    try:
        estadisticas = PuntosService.obtener_estadisticas_puntos(db)
        return estadisticas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas de puntos: {str(e)}"
        )


@router.post("/calcular/{pedido_id}")
def calcular_puntos_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calcula los puntos que se ganarían con un pedido específico.
    """
    try:
        puntos = PuntosService.calcular_puntos_por_pedido(db, pedido_id)
        return {
            "pedido_id": pedido_id,
            "puntos_calculados": puntos,
            "mensaje": f"El pedido #{pedido_id} otorgaría {puntos} puntos"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular puntos del pedido: {str(e)}"
        )


@router.post("/otorgar/{cliente_id}/{pedido_id}")
def otorgar_puntos_manual(
    cliente_id: int,
    pedido_id: int,
    puntos: int = Query(..., ge=1),
    descripcion: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Otorga puntos manualmente a un cliente por un pedido.
    Solo para uso administrativo.
    """
    try:
        movimiento = PuntosService.otorgar_puntos_por_pedido(
            db, cliente_id, pedido_id, puntos, descripcion
        )
        
        if movimiento:
            return {
                "exito": True,
                "mensaje": f"Se otorgaron {puntos} puntos al cliente {cliente_id}",
                "movimiento_id": movimiento.id
            }
        else:
            return {
                "exito": False,
                "mensaje": "No se pudieron otorgar los puntos"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al otorgar puntos: {str(e)}"
        )


@router.post("/estimar", response_model=EstimacionPuntosResponse)
def estimar_puntos_por_items(
    request: EstimacionPuntosRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Estima los puntos que se ganarían por una lista de productos.
    """
    try:
        estimacion = PuntosService.estimar_puntos_por_items(db, request.items)
        return estimacion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al estimar puntos: {str(e)}"
        )