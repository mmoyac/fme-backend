"""
Servicio para disparar webhooks externos (n8n) de forma asíncrona.
Fire-and-forget: no bloquea la respuesta al cliente si el webhook falla.
"""
import logging
import threading
import httpx
from sqlalchemy.orm import Session

from database.models import Pedido, Cotizacion
from services import notification_preferences_service

logger = logging.getLogger(__name__)

import os
N8N_WEBHOOK_PEDIDO_CONFIRMADO = "https://n8n.effi4tech.cl/webhook/pedido-confirmado"
N8N_WEBHOOK_PEDIDO_ENTREGADO = "https://n8n.effi4tech.cl/webhook/pedido-entregado"
N8N_WEBHOOK_COTIZACION_CREADA = "https://n8n.effi4tech.cl/webhook/cotizacion-creada"
N8N_WEBHOOK_COTIZACION_ENVIADA = "https://n8n.effi4tech.cl/webhook/cotizacion-enviada"
N8N_WEBHOOK_COTIZACION_ACEPTADA = "https://n8n.effi4tech.cl/webhook/cotizacion-aceptada"
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


def _build_cotizacion_payload(cotizacion: Cotizacion, db: Session) -> dict:
    from zoneinfo import ZoneInfo
    tz_cl = ZoneInfo("America/Santiago")
    cliente = cotizacion.cliente
    token_unsub = notification_preferences_service.get_token(db, cliente.id, "email") if cliente else None
    unsub_url = f"{API_BASE_URL}/api/clientes/unsubscribe?token={token_unsub}" if token_unsub else None
    fecha_cl = cotizacion.created_at.astimezone(tz_cl).strftime("%d/%m/%Y %H:%M") if cotizacion.created_at else None
    fecha_venc = cotizacion.fecha_vencimiento.strftime("%d/%m/%Y") if cotizacion.fecha_vencimiento else None
    tenant_nombre = cotizacion.tenant.nombre if cotizacion.tenant else "Nuestra tienda"
    version = cotizacion.version_activa

    return {
        "cotizacion_id": cotizacion.id,
        "numero_cotizacion": cotizacion.numero_cotizacion,
        "fecha": fecha_cl,
        "fecha_vencimiento": fecha_venc,
        "monto_total": float(version.monto_total) if version else 0.0,
        "cliente_nombre": f"{cliente.nombre} {cliente.apellido or ''}".strip() if cliente else "Cliente",
        "cliente_email": cliente.email if cliente else None,
        "cliente_telefono": cliente.telefono if cliente else None,
        "tenant_nombre": tenant_nombre,
        "unsub_url": unsub_url,
        "items": [
            {
                "producto": item.get("nombre", f"Producto {item.get('producto_id')}"),
                "cantidad": item.get("cantidad"),
                "precio_unitario": float(item.get("precio_unitario", 0)),
                "subtotal": float(item.get("subtotal", 0)),
            }
            for item in (version.items or [])
        ] if version else [],
    }


def _cotizacion_acepta_email(cotizacion: Cotizacion, db: Session) -> bool:
    if not cotizacion.cliente or not cotizacion.cliente.email:
        logger.info(f"Cotización {cotizacion.id} sin email de cliente, omitiendo webhook.")
        return False
    if not notification_preferences_service.acepta_canal(db, cotizacion.cliente.id, "email"):
        logger.info(f"Cliente {cotizacion.cliente.id} no acepta emails, omitiendo webhook cotización.")
        return False
    return True


def trigger_cotizacion_creada(cotizacion: Cotizacion, db: Session) -> None:
    """Dispara el webhook cuando se crea una cotización. Fire-and-forget."""
    if not _cotizacion_acepta_email(cotizacion, db):
        return
    payload = _build_cotizacion_payload(cotizacion, db)
    threading.Thread(target=_post_webhook, args=(N8N_WEBHOOK_COTIZACION_CREADA, payload), daemon=True).start()


def trigger_cotizacion_enviada(cotizacion: Cotizacion, db: Session) -> None:
    """Dispara el webhook cuando la cotización es enviada al cliente. Fire-and-forget."""
    if not _cotizacion_acepta_email(cotizacion, db):
        return
    payload = _build_cotizacion_payload(cotizacion, db)
    payload["version_numero"] = cotizacion.version_activa.numero_version if cotizacion.version_activa else 1
    threading.Thread(target=_post_webhook, args=(N8N_WEBHOOK_COTIZACION_ENVIADA, payload), daemon=True).start()


def trigger_cotizacion_aceptada(cotizacion: Cotizacion, db: Session, numero_pedido: str, estado_pedido: str, costo_delivery: float | None = None) -> None:
    """Dispara el webhook cuando la cotización es aceptada y el pedido fue generado. Fire-and-forget."""
    if not _cotizacion_acepta_email(cotizacion, db):
        return
    payload = _build_cotizacion_payload(cotizacion, db)
    payload["numero_pedido"] = numero_pedido
    payload["estado_pedido"] = estado_pedido
    payload["costo_delivery"] = costo_delivery
    payload["tiene_delivery"] = costo_delivery is not None
    threading.Thread(target=_post_webhook, args=(N8N_WEBHOOK_COTIZACION_ACEPTADA, payload), daemon=True).start()
