"""
Servicio para disparar webhooks externos (n8n) de forma asíncrona.
Fire-and-forget: no bloquea la respuesta al cliente si el webhook falla.
"""
import asyncio
import logging
import httpx
from sqlalchemy.orm import Session

from database.models import Pedido
from services import notification_preferences_service

logger = logging.getLogger(__name__)

N8N_WEBHOOK_PEDIDO_CONFIRMADO = "https://n8n.masasestacion.cl/webhook/pedido-confirmado"
API_BASE_URL = "https://api.masasestacion.cl"


def _build_pedido_payload(pedido: Pedido, db: Session) -> dict:
    cliente = pedido.cliente
    token_unsub = notification_preferences_service.get_token(db, cliente.id, "email") if cliente else None
    unsub_url = f"{API_BASE_URL}/api/clientes/unsubscribe?token={token_unsub}" if token_unsub else None

    return {
        "pedido_id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "fecha_pedido": pedido.fecha_pedido.isoformat() if pedido.fecha_pedido else None,
        "monto_total": float(pedido.monto_total or 0),
        "cliente_nombre": f"{cliente.nombre} {cliente.apellido or ''}".strip() if cliente else "Cliente",
        "cliente_email": cliente.email if cliente else None,
        "cliente_telefono": cliente.telefono if cliente else None,
        "unsub_url": unsub_url,
        "items": [
            {
                "producto": item.producto.nombre if item.producto else f"Producto {item.producto_id}",
                "cantidad": item.cantidad,
                "precio_unitario": float(item.precio_unitario or 0),
                "subtotal": float((item.precio_unitario or 0) * item.cantidad),
            }
            for item in (pedido.items or [])
        ],
    }


async def _post_webhook(url: str, payload: dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.warning(f"Webhook {url} falló (ignorado): {e}")


def trigger_pedido_confirmado(pedido: Pedido, db: Session) -> None:
    """Dispara el webhook de pedido confirmado. Fire-and-forget."""
    if not pedido.cliente or not pedido.cliente.email:
        logger.info(f"Pedido {pedido.id} sin email de cliente, omitiendo webhook.")
        return

    if not notification_preferences_service.acepta_canal(db, pedido.cliente.id, "email"):
        logger.info(f"Cliente {pedido.cliente.id} no acepta emails, omitiendo webhook.")
        return

    payload = _build_pedido_payload(pedido, db)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_post_webhook(N8N_WEBHOOK_PEDIDO_CONFIRMADO, payload))
        else:
            loop.run_until_complete(_post_webhook(N8N_WEBHOOK_PEDIDO_CONFIRMADO, payload))
    except Exception as e:
        logger.warning(f"No se pudo disparar webhook pedido confirmado: {e}")
