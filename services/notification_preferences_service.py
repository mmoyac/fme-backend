"""
Servicio para gestionar preferencias de notificación por canal de los clientes.
"""
import secrets
from sqlalchemy.orm import Session
from database.models import ClienteNotificationPreference

CANALES_DEFAULT = ["email", "whatsapp", "telegram", "sms"]


def crear_preferencias_default(db: Session, cliente_id: int) -> None:
    """Crea las preferencias por defecto (activo=True) para todos los canales al crear un cliente."""
    for canal in CANALES_DEFAULT:
        pref = ClienteNotificationPreference(
            cliente_id=cliente_id,
            canal=canal,
            activo=True,
            token_unsub=secrets.token_hex(32),
        )
        db.add(pref)
    db.commit()


def acepta_canal(db: Session, cliente_id: int, canal: str) -> bool:
    """Retorna True si el cliente acepta notificaciones por ese canal."""
    pref = (
        db.query(ClienteNotificationPreference)
        .filter_by(cliente_id=cliente_id, canal=canal)
        .first()
    )
    if not pref:
        return True  # sin preferencia registrada → asumimos activo
    return pref.activo


def get_token(db: Session, cliente_id: int, canal: str) -> str | None:
    """Retorna el token de desuscripción para el canal dado."""
    pref = (
        db.query(ClienteNotificationPreference)
        .filter_by(cliente_id=cliente_id, canal=canal)
        .first()
    )
    return pref.token_unsub if pref else None


def toggle_suscripcion(db: Session, token: str) -> dict | None:
    """Alterna el estado activo/inactivo por token. Retorna el estado resultante."""
    pref = (
        db.query(ClienteNotificationPreference)
        .filter_by(token_unsub=token)
        .first()
    )
    if not pref:
        return None
    pref.activo = not pref.activo
    db.commit()
    db.refresh(pref)
    return {"canal": pref.canal, "activo": pref.activo}
