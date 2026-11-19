"""Registro de la entrega de un pedido (change add-modalidad-entrega-pedido).

Punto único para pasar un pedido a ENTREGADO y dejar trazabilidad de quién y cuándo,
sea retiro en local, hoja de ruta, despacho, POS directo o cambio manual de estado.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import models

MODALIDADES = ("RETIRO", "DESPACHO")


def modalidad_desde_request(modalidad: Optional[str], requiere_delivery: Optional[bool]) -> str:
    """Modalidad explícita si viene; si no, se deriva de requiere_delivery (compatibilidad)."""
    if modalidad:
        m = modalidad.strip().upper()
        if m in MODALIDADES:
            return m
    return "DESPACHO" if requiere_delivery else "RETIRO"


def registrar_entrega(
    db: Session,
    pedido: "models.Pedido",
    usuario_id: Optional[int],
    *,
    cambiar_estado: bool = True,
    fecha: Optional[datetime] = None,
    retirado_por_nombre: Optional[str] = None,
    retirado_por_rut: Optional[str] = None,
    nota: Optional[str] = None,
) -> None:
    """Marca la entrega. Idempotente: si ya tiene fecha_entrega, no la pisa."""
    if cambiar_estado:
        estado = db.query(models.EstadoPedido).filter(models.EstadoPedido.codigo == "ENTREGADO").first()
        if estado:
            pedido.estado_id = estado.id
    if pedido.fecha_entrega is None:
        pedido.fecha_entrega = fecha or datetime.now(timezone.utc)
        pedido.entregado_por_id = usuario_id
    if retirado_por_nombre:
        pedido.retirado_por_nombre = retirado_por_nombre.strip()[:120]
    if retirado_por_rut:
        pedido.retirado_por_rut = retirado_por_rut.strip()[:12]
    if nota:
        pedido.nota_entrega = nota.strip()


def datos_entrega(pedido) -> dict:
    """Campos de entrega para las respuestas de pedido/cobranza."""
    ep = getattr(pedido, "entregado_por", None)
    return {
        "modalidad_entrega": pedido.modalidad_entrega,
        "fecha_entrega": pedido.fecha_entrega,
        "entregado_por_id": pedido.entregado_por_id,
        "entregado_por_nombre": (ep.nombre_completo or ep.email) if ep else None,
        "retirado_por_nombre": pedido.retirado_por_nombre,
        "retirado_por_rut": pedido.retirado_por_rut,
        "nota_entrega": pedido.nota_entrega,
        # add-delivery-por-comuna
        "comuna_entrega": getattr(pedido, "comuna_entrega", None),
        "costo_delivery": float(pedido.costo_delivery) if pedido.costo_delivery else None,
    }
