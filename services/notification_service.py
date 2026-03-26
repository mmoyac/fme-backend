"""
Servicio de notificaciones internas con SSE (Server-Sent Events).

Arquitectura (single worker, sin Redis):
  - _connections: dict {user_id: asyncio.Queue} con las conexiones SSE activas.
  - notify(): guarda en DB y pone el evento en la Queue del usuario si está conectado.
  - sse_generator(): generador async que lee de la Queue y emite eventos SSE.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from database.models import Notification, User, Role

# Mapa de conexiones SSE activas: user_id → asyncio.Queue
_connections: dict[int, asyncio.Queue] = {}


def _get_admins_for_local(db: Session, tenant_id: int, local_id: int) -> list[int]:
    """Retorna user_ids de: admin del local + superadmins del tenant."""
    users = (
        db.query(User.id)
        .join(Role, User.role_id == Role.id)
        .filter(
            User.tenant_id == tenant_id,
            User.is_active == True,
            (
                # Admin del local origen
                ((Role.nombre == "admin") & (User.local_defecto_id == local_id)) |
                # Superadmin
                (User.is_superadmin == True)
            ),
        )
        .all()
    )
    return [u.id for u in users]


def notify_solicitud_creada(
    db: Session,
    tenant_id: int,
    local_origen_id: int,
    local_origen_nombre: str,
    solicitud_id: int,
    solicitante_nombre: str,
) -> None:
    """Crea notificaciones para admins del local origen y superadmins."""
    user_ids = _get_admins_for_local(db, tenant_id, local_origen_id)

    notifications = []
    for user_id in user_ids:
        notif = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type="solicitud_creada",
            title="Nueva solicitud de transferencia",
            body=f"{solicitante_nombre} creó una solicitud desde {local_origen_nombre}",
            payload={"solicitud_id": solicitud_id, "local_origen_id": local_origen_id},
            action_url=f"/admin/solicitudes",
        )
        notifications.append(notif)
        db.add(notif)

    db.commit()

    # Emitir SSE a usuarios conectados
    for notif in notifications:
        db.refresh(notif)
        _push_sse(notif.user_id, notif)


def _push_sse(user_id: int, notif: Notification) -> None:
    """Pone el evento en la Queue del usuario si está conectado."""
    queue = _connections.get(user_id)
    if queue:
        data = {
            "id": notif.id,
            "type": notif.type,
            "title": notif.title,
            "body": notif.body,
            "payload": notif.payload,
            "action_url": notif.action_url,
            "created_at": notif.created_at.isoformat(),
        }
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            pass


async def sse_generator(user_id: int) -> AsyncGenerator[str, None]:
    """Generador SSE para un usuario. Se registra y escucha su Queue."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _connections[user_id] = queue
    try:
        # Heartbeat cada 30s para mantener la conexión viva
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
    finally:
        _connections.pop(user_id, None)


def _get_users_of_local(db: Session, tenant_id: int, local_id: int) -> list[int]:
    """Retorna user_ids de todos los usuarios activos asignados a un local."""
    users = (
        db.query(User.id)
        .filter(
            User.tenant_id == tenant_id,
            User.local_defecto_id == local_id,
            User.is_active == True,
        )
        .all()
    )
    return [u.id for u in users]


def notify_solicitud_en_proceso(
    db: Session,
    tenant_id: int,
    local_destino_id: int,
    solicitud_id: int,
    local_origen_nombre: str,
) -> None:
    """Notifica al local destino que su solicitud está siendo atendida."""
    user_ids = _get_users_of_local(db, tenant_id, local_destino_id)
    notifications = []
    for user_id in user_ids:
        notif = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type="solicitud_en_proceso",
            title="Solicitud en proceso",
            body=f"{local_origen_nombre} está atendiendo tu solicitud #{solicitud_id}",
            payload={"solicitud_id": solicitud_id},
            action_url="/admin/solicitudes",
        )
        notifications.append(notif)
        db.add(notif)
    db.commit()
    for notif in notifications:
        db.refresh(notif)
        _push_sse(notif.user_id, notif)


def notify_solicitud_finalizada(
    db: Session,
    tenant_id: int,
    local_destino_id: int,
    solicitud_id: int,
    local_origen_nombre: str,
) -> None:
    """Notifica al local destino que su solicitud fue aprobada y despachada."""
    user_ids = _get_users_of_local(db, tenant_id, local_destino_id)
    notifications = []
    for user_id in user_ids:
        notif = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type="solicitud_finalizada",
            title="Solicitud aprobada y despachada",
            body=f"{local_origen_nombre} despachó tu solicitud #{solicitud_id}",
            payload={"solicitud_id": solicitud_id},
            action_url="/admin/solicitudes",
        )
        notifications.append(notif)
        db.add(notif)
    db.commit()
    for notif in notifications:
        db.refresh(notif)
        _push_sse(notif.user_id, notif)


def mark_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
    """Marca una notificación como leída. Retorna None si no pertenece al usuario."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notif:
        return None
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications(db: Session, user_id: int, limit: int = 30) -> list[Notification]:
    """Retorna las últimas notificaciones del usuario."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: int) -> int:
    """Retorna el conteo de notificaciones no leídas."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at == None)
        .count()
    )
