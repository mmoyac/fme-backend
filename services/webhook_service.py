"""
Servicio para disparar webhooks externos (n8n) de forma asíncrona.
Fire-and-forget: no bloquea la respuesta al cliente si el webhook falla.
"""
import logging
import threading
import httpx
from sqlalchemy.orm import Session

from database.models import Pedido
from services import notification_preferences_service

logger = logging.getLogger(__name__)

import os
N8N_WEBHOOK_PEDIDO_CONFIRMADO = "https://n8n.masasestacion.cl/webhook/pedido-confirmado"
N8N_WEBHOOK_PEDIDO_ENTREGADO = "https://n8n.masasestacion.cl/webhook/pedido-entregado"
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.masasestacion.cl")


def _build_pedido_payload(pedido: Pedido, db: Session) -> dict:
    from zoneinfo import ZoneInfo
    tz_cl = ZoneInfo("America/Santiago")
    cliente = pedido.cliente
    token_unsub = notification_preferences_service.get_token(db, cliente.id, "email") if cliente else None
    unsub_url = f"{API_BASE_URL}/api/clientes/unsubscribe?token={token_unsub}" if token_unsub else None
    seguimiento_url = f"https://seguimiento.lexastech.cl/{pedido.token_seguimiento}" if pedido.token_seguimiento else None
    fecha_cl = pedido.fecha_pedido.astimezone(tz_cl).strftime("%d/%m/%Y %H:%M") if pedido.fecha_pedido else None

    tenant_nombre = pedido.tenant.nombre if pedido.tenant else "Nuestra tienda"

    return {
        "pedido_id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "fecha_pedido": fecha_cl,
        "monto_total": float(pedido.monto_total or 0),
        "cliente_nombre": f"{cliente.nombre} {cliente.apellido or ''}".strip() if cliente else "Cliente",
        "cliente_email": cliente.email if cliente else None,
        "cliente_telefono": cliente.telefono if cliente else None,
        "tenant_nombre": tenant_nombre,
        "unsub_url": unsub_url,
        "seguimiento_url": seguimiento_url,
        "items": [
            {
                "producto": item.producto.nombre if item.producto else f"Producto {item.producto_id}",
                "cantidad": item.cantidad,
                "precio_unitario": float(item.precio_unitario_venta or 0),
                "subtotal": float((item.precio_unitario_venta or 0) * item.cantidad),
            }
            for item in (pedido.items or [])
        ],
    }


def _post_webhook(url: str, payload: dict) -> None:
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json=payload)
    except Exception as e:
        logger.warning(f"Webhook {url} falló (ignorado): {e}")


def trigger_pedido_confirmado(pedido: Pedido, db: Session) -> None:
    """Dispara el webhook de pedido confirmado. Fire-and-forget."""
    if not pedido.cliente or not pedido.cliente.email:
        logger.info(f"Pedido {pedido.id} sin email de cliente, omitiendo webhook.")
        return

    if pedido.canal_venta and pedido.canal_venta.entrega_inmediata:
        logger.info(f"Pedido {pedido.id} con entrega inmediata (canal {pedido.canal_venta.codigo}), omitiendo email.")
        return

    if not notification_preferences_service.acepta_canal(db, pedido.cliente.id, "email"):
        logger.info(f"Cliente {pedido.cliente.id} no acepta emails, omitiendo webhook.")
        return

    payload = _build_pedido_payload(pedido, db)

    thread = threading.Thread(
        target=_post_webhook,
        args=(N8N_WEBHOOK_PEDIDO_CONFIRMADO, payload),
        daemon=True
    )
    thread.start()


def trigger_pedido_entregado(pedido: Pedido, db: Session, fecha_entrega=None) -> None:
    """Dispara el webhook de pedido entregado. Fire-and-forget."""
    if not pedido.cliente or not pedido.cliente.email:
        logger.info(f"Pedido {pedido.id} sin email de cliente, omitiendo webhook entrega.")
        return

    if not notification_preferences_service.acepta_canal(db, pedido.cliente.id, "email"):
        logger.info(f"Cliente {pedido.cliente.id} no acepta emails, omitiendo webhook entrega.")
        return

    from zoneinfo import ZoneInfo
    tz_cl = ZoneInfo("America/Santiago")
    cliente = pedido.cliente
    token_unsub = notification_preferences_service.get_token(db, cliente.id, "email")
    unsub_url = f"{API_BASE_URL}/api/clientes/unsubscribe?token={token_unsub}" if token_unsub else None
    fecha_str = fecha_entrega.astimezone(tz_cl).strftime("%d/%m/%Y %H:%M") if fecha_entrega else None

    payload = {
        "pedido_id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "fecha_entrega": fecha_str,
        "monto_total": float(pedido.monto_total or 0),
        "cliente_nombre": f"{cliente.nombre} {cliente.apellido or ''}".strip(),
        "cliente_email": cliente.email,
        "unsub_url": unsub_url,
    }

    thread = threading.Thread(
        target=_post_webhook,
        args=(N8N_WEBHOOK_PEDIDO_ENTREGADO, payload),
        daemon=True
    )
    thread.start()
