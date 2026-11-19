"""Tarifas de delivery por comuna (change add-delivery-por-comuna).

- Público (landing, tenant por dominio): GET /api/tienda/entrega
- Administración (rol admin, tenant del usuario, módulo tienda_online): /api/admin/tarifas-delivery
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import ConfiguracionLanding, TarifaDelivery
from services.tarifas_delivery import monto_minimo_gratis, normalizar_comuna
from services.tenant_service import get_tenant_from_request
from utils.permisos import ROLES_ADMIN, require_roles

router = APIRouter()
admin_router = APIRouter()


# ----------------------------------------------------------------------------- público
@router.get("/entrega")
def opciones_entrega(request: Request, db: Session = Depends(get_db)):
    """Opciones de entrega del checkout: dirección de retiro, comunas con delivery y monto mínimo para envío gratis."""
    tenant = get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(404, "Tienda no encontrada")
    conf = db.query(ConfiguracionLanding).filter(ConfiguracionLanding.tenant_id == tenant.id).first()
    tarifas = (db.query(TarifaDelivery)
               .filter(TarifaDelivery.tenant_id == tenant.id, TarifaDelivery.activo.is_(True))
               .order_by(TarifaDelivery.comuna_normalizada).all())
    minimo = monto_minimo_gratis(db, tenant.id)
    return {
        "retiro": {"direccion": conf.direccion if conf else None},
        "tarifas": [{"comuna": t.comuna, "costo": int(t.costo)} for t in tarifas],
        "monto_minimo_gratis": int(minimo) if minimo is not None else None,
        # Si es False, el checkout no ofrece "Solicitar pedido sin pagar ahora" (add-interruptor-pedido-sin-pago)
        "permite_pedido_sin_pago": conf.permitir_pedido_sin_pago if conf else True,
    }


# ----------------------------------------------------------------------------- administración
_rol_admin = require_roles(ROLES_ADMIN)


def admin(user=Depends(_rol_admin)):
    if not user.tenant_id:
        raise HTTPException(400, "Seleccione un tenant (Superadmin → Operar en tenant) para configurar sus tarifas de delivery")
    return user


class TarifaIn(BaseModel):
    comuna: str = Field(min_length=2, max_length=100)
    costo: int = Field(ge=0, le=1_000_000)
    activo: bool = True


def _salida(t: TarifaDelivery) -> dict:
    return {"id": t.id, "comuna": t.comuna, "costo": int(t.costo), "activo": t.activo, "updated_at": t.updated_at}


def _tarifa(db: Session, user, tarifa_id: int) -> TarifaDelivery:
    t = db.query(TarifaDelivery).filter(TarifaDelivery.id == tarifa_id, TarifaDelivery.tenant_id == user.tenant_id).first()
    if not t:
        raise HTTPException(404, "Tarifa no encontrada")
    return t


def _validar_unica(db: Session, tenant_id: int, clave: str, excepto_id: int | None = None) -> None:
    q = db.query(TarifaDelivery).filter(TarifaDelivery.tenant_id == tenant_id, TarifaDelivery.comuna_normalizada == clave)
    if excepto_id:
        q = q.filter(TarifaDelivery.id != excepto_id)
    if q.first():
        raise HTTPException(409, "Ya existe una tarifa para esa comuna")


@admin_router.get("")
def listar(db: Session = Depends(get_db), user=Depends(admin)):
    q = db.query(TarifaDelivery).filter(TarifaDelivery.tenant_id == user.tenant_id).order_by(TarifaDelivery.comuna_normalizada)
    return [_salida(t) for t in q]


@admin_router.post("", status_code=201)
def crear(datos: TarifaIn, db: Session = Depends(get_db), user=Depends(admin)):
    comuna = " ".join(datos.comuna.split())
    clave = normalizar_comuna(comuna)
    _validar_unica(db, user.tenant_id, clave)
    t = TarifaDelivery(tenant_id=user.tenant_id, comuna=comuna, comuna_normalizada=clave, costo=datos.costo,
                       activo=datos.activo)
    db.add(t)
    db.commit()
    db.refresh(t)
    return _salida(t)


@admin_router.put("/{tarifa_id}")
def editar(tarifa_id: int, datos: TarifaIn, db: Session = Depends(get_db), user=Depends(admin)):
    t = _tarifa(db, user, tarifa_id)
    comuna = " ".join(datos.comuna.split())
    clave = normalizar_comuna(comuna)
    _validar_unica(db, user.tenant_id, clave, excepto_id=t.id)
    t.comuna, t.comuna_normalizada, t.costo, t.activo = comuna, clave, datos.costo, datos.activo
    db.commit()
    db.refresh(t)
    return _salida(t)


@admin_router.delete("/{tarifa_id}", status_code=204)
def eliminar(tarifa_id: int, db: Session = Depends(get_db), user=Depends(admin)):
    t = _tarifa(db, user, tarifa_id)
    db.delete(t)
    db.commit()
