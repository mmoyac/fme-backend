"""
Router para configuraciones y datos básicos del sistema (sin autenticación).
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db

router = APIRouter()


@router.get("/tipos-documento")
def listar_tipos_documento(
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Listar tipos de documento tributario disponibles.
    Endpoint público necesario para el frontend.
    """
    from database.models import TipoDocumento
    
    query = db.query(TipoDocumento)
    
    if activo is not None:
        query = query.filter(TipoDocumento.activo == activo)
    
    tipos = query.order_by(TipoDocumento.nombre).all()
    
    return [
        {
            "id": tipo.id,
            "codigo": tipo.codigo,
            "nombre": tipo.nombre,
            "descripcion": tipo.descripcion,
            "activo": tipo.activo
        }
        for tipo in tipos
    ]


@router.get("/medios-pago")
def listar_medios_pago(
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Listar medios de pago disponibles.
    Endpoint público necesario para el frontend.
    """
    from database.models import MedioPago
    
    query = db.query(MedioPago)
    
    if activo is not None:
        query = query.filter(MedioPago.activo == activo)
    
    medios = query.order_by(MedioPago.nombre).all()
    
    return [
        {
            "id": medio.id,
            "codigo": medio.codigo,
            "nombre": medio.nombre,
            "descripcion": medio.descripcion,
            "permite_cheque": medio.permite_cheque,
            "activo": medio.activo
        }
        for medio in medios
    ]