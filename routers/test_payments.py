
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Pedido

router = APIRouter()

@router.post("/test_webhook/{pedido_id}")
async def test_webhook_simulation(pedido_id: int, db: Session = Depends(get_db)):
    """
    ENDPOINT TEMPORAL DE PRUEBA - Simula un pago aprobado sin consultar a Mercado Pago.
    ⚠️ ELIMINAR EN PRODUCCIÓN
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    
    if not pedido:
        return {"error": "Pedido no encontrado"}
    
    # Simular pago aprobado
    pedido.mp_payment_id = "TEST_PAYMENT_12345"
    pedido.mp_status = "approved"
    pedido.es_pagado = True
    pedido.estado = "CONFIRMADO"
    
    db.commit()
    
    return {
        "status": "ok",
        "message": "Pedido marcado como pagado (SIMULACIÓN)",
        "pedido_id": pedido.id,
        "es_pagado": pedido.es_pagado,
        "estado": pedido.estado
    }
