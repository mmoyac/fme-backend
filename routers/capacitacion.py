"""Centro de Capacitación: índice y contenido de lecciones (change add-centro-capacitacion).

Autenticación a nivel router (main.py). El módulo viene en la URL, así que el control por
módulo contratado se hace aquí y no con require_modulo. Todo `def` síncrono (BD síncrona).
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User
from routers.auth import get_current_active_user
from services import capacitacion_service as svc
from utils.modulos import error_modulo_no_contratado, modulos_de_tenant, tenant_de_request

router = APIRouter()


def _modulos_visibles(request: Request, db: Session, user: User) -> Optional[set[str]]:
    """None = ve todo (superadmin sin tenant impersonado)."""
    tenant_id = tenant_de_request(request, db)
    if tenant_id is None and user.is_superadmin:
        return None
    return modulos_de_tenant(db, tenant_id)


@router.get("")
def indice(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    return {"secciones": svc.secciones_visibles(_modulos_visibles(request, db, current_user))}


@router.get("/{modulo}/{slug}", response_class=HTMLResponse)
def leccion(
    modulo: str,
    slug: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    if not svc.es_modulo_conocido(modulo):
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    visibles = _modulos_visibles(request, db, current_user)
    if visibles is not None and modulo != svc.GENERAL and modulo not in visibles:
        raise error_modulo_no_contratado(modulo)
    html = svc.leer_leccion(modulo, slug)
    if html is None:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
