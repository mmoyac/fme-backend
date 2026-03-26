
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Pedido
from services.payment_service import payment_service
from services.webhook_service import trigger_pedido_confirmado
from routers.auth import get_current_active_user
from routers.pedidos import descontar_inventario

router = APIRouter()

@router.post("/create_preference/{pedido_id}")
async def create_payment_preference(
    pedido_id: int, 
    db: Session = Depends(get_db)
    # Sin auth, o con auth según prefieras. Normalmente es público si viene del frontend tras crear pedido.
    # Pero idealmente aseguramos que el pedido pertenezca al usuario (si hay login) o sea recién creado.
    # Por ahora lo dejamos abierto pero validando existencia.
):
    """
    Genera un link de pago (Preferencia) para un pedido existente.
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if pedido.es_pagado:
        raise HTTPException(status_code=400, detail="El pedido ya está pagado")

    # Crear preferencia en MP
    try:
        preference = payment_service.create_preference(pedido)
        
        # Guardar ID de preferencia para referencia
        pedido.mp_preference_id = preference["id"]
        db.commit()
        
        return {"preference_id": preference["id"], "init_point": preference["init_point"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process_payment")
async def process_payment(request: Request, db: Session = Depends(get_db)):
    """
    Procesa el pago enviado por el Payment Brick.
    """
    try:
        body = await request.json()
        
        # Opcional: Validar que el monto coincida con el pedido si se envía 'external_reference'
        # Pero MP ya valida algunas cosas.
        
        payment_result = payment_service.process_payment(body)
        
        # Si el pago es aprobado, actualizamos el pedido inmediatamente
        if payment_result.get("status") == "approved":
            external_ref = payment_result.get("external_reference")
            if external_ref:
                pedido = db.query(Pedido).filter(Pedido.id == int(external_ref)).first()
                if pedido and not pedido.es_pagado:
                    pedido.es_pagado = True
                    pedido.estado = "CONFIRMADO"
                    pedido.mp_payment_id = str(payment_result.get("id"))
                    pedido.mp_status = "approved"
                    db.commit()
                    db.refresh(pedido)
                    trigger_pedido_confirmado(pedido)
        
        return payment_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def mercado_pago_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe notificaciones de Mercado Pago.
    """
    # Mercado Pago puede mandar los datos por query params o body
    query_params = request.query_params
    topic = query_params.get("topic") or query_params.get("type")
    mp_id = query_params.get("id") or query_params.get("data.id")

    # A veces viene en el body
    if not topic or not mp_id:
        try:
            body = await request.json()
            topic = body.get("type")
            data = body.get("data", {})
            mp_id = data.get("id")
        except:
            pass

    if topic == "payment" and mp_id:
        # Consultar estado real del pago a MP (Seguridad: No confiar ciegamente en el webhook)
        payment_info = payment_service.check_payment(mp_id)
        
        if payment_info:
            external_ref = payment_info.get("external_reference") # ID de nuestro pedido
            status_detail = payment_info.get("status")
            
            if external_ref:
                pedido = db.query(Pedido).filter(Pedido.id == int(external_ref)).first()
                if pedido:
                    # Actualizar info de pago
                    pedido.mp_payment_id = str(mp_id)
                    pedido.mp_status = status_detail
                    
                    # Si está aprobado y no estaba pagado previamente
                    if status_detail == "approved" and not pedido.es_pagado:
                        pedido.es_pagado = True
                        pedido.estado = "CONFIRMADO"
                        db.flush()
                        db.refresh(pedido)
                        trigger_pedido_confirmado(pedido)

                    db.commit()
                    return {"status": "ok"}
    
    return {"status": "ignored"}
