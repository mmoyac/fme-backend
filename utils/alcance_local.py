"""
Regla de alcance por local en el módulo de inventario (change OpenSpec: add-inventario-alcance-por-local).

- Alcance total: superadmin, rol "admin" o usuario sin local asignado → opera sobre todos los locales.
- Alcance de local: cualquier otro usuario → solo su `local_defecto_id`.
"""
from typing import Optional

from fastapi import HTTPException, status


def es_admin(user) -> bool:
    return bool(getattr(user, "is_superadmin", False) or (user.role and user.role.nombre.lower() == "admin"))


def local_de_alcance(user) -> Optional[int]:
    """None = alcance total; si no, el id del único local sobre el que puede operar."""
    if es_admin(user) or not user.local_defecto_id:
        return None
    return user.local_defecto_id


def exigir_local(user, local_id: Optional[int]) -> None:
    """403 si el usuario tiene alcance de local y `local_id` no es el suyo."""
    propio = local_de_alcance(user)
    if propio is not None and local_id != propio:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a ese local")
