"""
Router de notificaciones internas con SSE.

Endpoints:
  GET  /api/notifications          → lista de notificaciones del usuario
  GET  /api/notifications/count    → conteo de no leídas (badge)
  PATCH /api/notifications/{id}/read → marcar como leída
  GET  /api/notifications/stream   → stream SSE
  DELETE /api/notifications/cleanup → limpieza periódica (API Key)
"""
import os
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone, timedelta

from database.database import get_db, SessionLocal
from database.models import User, Notification
from routers.auth import get_current_active_user
from services import notification_service

INTEGRATION_API_KEY = os.getenv("INTEGRATION_API_KEY")

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = notification_service.get_unread_count(db, current_user.id)
    return {"unread": count}


@router.get("/")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notifications = notification_service.get_notifications(db, current_user.id)
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "payload": n.payload,
            "action_url": n.action_url,
            "read_at": n.read_at,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    notif = notification_service.mark_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    return {"id": notif.id, "read_at": notif.read_at}


@router.delete("/cleanup")
def cleanup_notifications(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Limpieza periódica de notificaciones antiguas. Requiere API Key.
    - Leídas con más de 30 días → eliminadas
    - No leídas con más de 90 días → eliminadas
    """
    if not INTEGRATION_API_KEY or x_api_key != INTEGRATION_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key inválida")

    now = datetime.now(timezone.utc)
    deleted_read = db.query(Notification).filter(
        and_(Notification.read_at != None, Notification.read_at < now - timedelta(days=30))
    ).delete(synchronize_session=False)

    deleted_unread = db.query(Notification).filter(
        and_(Notification.read_at == None, Notification.created_at < now - timedelta(days=90))
    ).delete(synchronize_session=False)

    db.commit()
    return {
        "deleted_read": deleted_read,
        "deleted_unread": deleted_unread,
        "total_deleted": deleted_read + deleted_unread,
    }


@router.get("/stream")
def sse_stream(token: str):
    """Stream SSE. Acepta el token por query param porque EventSource no soporta headers custom.
    Ejemplo: GET /api/notifications/stream?token=eyJ...

    No usa Depends(get_db): con FastAPI 0.104 la sesión de una dependencia con yield
    se cierra recién cuando termina la respuesta, y un stream SSE dura horas, así que
    cada pestaña abierta retendría una conexión del pool. La sesión se abre y se cierra
    aquí mismo, antes de empezar el stream.
    """
    from jose import JWTError, jwt
    from utils.security import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    db = SessionLocal()
    try:
        row = (
            db.query(User.id)
            .filter(User.email == email, User.is_active == True)
            .first()
        )
    finally:
        db.close()
    user_id = row[0] if row else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    return StreamingResponse(
        notification_service.sse_generator(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # necesario para nginx
        },
    )
