"""Validación de rol a nivel de endpoint.

El RBAC de menús (role_menu_permissions) solo controla qué ve el usuario en el
backoffice; estas helpers protegen las acciones en el backend.
"""
from typing import Iterable

from fastapi import Depends, HTTPException, status

from routers.auth import get_current_active_user

ROLES_ADMIN = frozenset({"admin", "administrador", "superadmin"})
ROLES_PRODUCCION = ROLES_ADMIN | {"produccion"}


def rol_de(user) -> str:
    return (user.role.nombre if user and user.role else "").strip().lower()


def verificar_rol(user, roles: Iterable[str]) -> None:
    """Lanza 403 si el rol del usuario no está en `roles` (comparación case-insensitive)."""
    if getattr(user, "is_superadmin", False):
        return
    if rol_de(user) not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu rol no tiene permiso para realizar esta acción",
        )


def require_roles(roles: Iterable[str]):
    """Dependencia FastAPI: retorna el usuario actual si su rol está permitido.

    Síncrona a propósito (ver incidente event loop: nada async con BD síncrona).
    """
    roles = frozenset(r.lower() for r in roles)

    def _dep(current_user=Depends(get_current_active_user)):
        verificar_rol(current_user, roles)
        return current_user

    return _dep


ROLES_SOLO_EJECUCION = frozenset({"produccion"})


def bloquear_roles(user, roles: Iterable[str] = ROLES_SOLO_EJECUCION) -> None:
    """403 si el rol del usuario está en `roles`.

    Uso: el rol `produccion` solo ejecuta/finaliza; no crea, edita ni cancela OT.
    """
    if getattr(user, "is_superadmin", False):
        return
    if rol_de(user) in {r.lower() for r in roles}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu rol solo puede finalizar órdenes, no crearlas ni modificarlas",
        )
