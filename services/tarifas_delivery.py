"""Tarifas de delivery por comuna (change add-delivery-por-comuna).

El costo de delivery de un pedido de la tienda lo calcula SIEMPRE el backend desde esta tabla; nunca se confía en un
monto enviado por el navegador.
"""
import unicodedata
from decimal import Decimal

from sqlalchemy.orm import Session

from database.models import ConfiguracionLanding, TarifaDelivery

MODALIDADES = ("RETIRO", "DESPACHO")


class ErrorEntrega(Exception):
    """Modalidad o comuna inválida para el pedido."""


def normalizar_comuna(nombre: str | None) -> str:
    """Minúsculas, sin tildes y con espacios simples: 'Ñuñoa ' y 'ñuñoa' son la misma comuna."""
    s = unicodedata.normalize("NFKD", (nombre or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.split())


def tarifa_de(db: Session, tenant_id: int, comuna: str | None) -> TarifaDelivery | None:
    clave = normalizar_comuna(comuna)
    if not clave:
        return None
    return (db.query(TarifaDelivery)
            .filter(TarifaDelivery.tenant_id == tenant_id, TarifaDelivery.comuna_normalizada == clave,
                    TarifaDelivery.activo.is_(True))
            .first())


def monto_minimo_gratis(db: Session, tenant_id: int) -> Decimal | None:
    conf = db.query(ConfiguracionLanding).filter(ConfiguracionLanding.tenant_id == tenant_id).first()
    if conf and conf.monto_minimo_delivery_gratis is not None and conf.monto_minimo_delivery_gratis > 0:
        return Decimal(conf.monto_minimo_delivery_gratis)
    return None


def costo_delivery(db: Session, tenant_id: int, modalidad: str, comuna: str | None,
                   monto_productos: float | Decimal) -> tuple[Decimal, str | None]:
    """Devuelve (costo, nombre de la comuna tal como está en la tarifa). RETIRO → (0, None).

    Lanza ErrorEntrega si la modalidad no es válida o la comuna no tiene tarifa activa.
    """
    modalidad = (modalidad or "").strip().upper()
    if modalidad not in MODALIDADES:
        raise ErrorEntrega("Modalidad de entrega inválida (RETIRO o DESPACHO)")
    if modalidad == "RETIRO":
        return Decimal("0"), None
    tarifa = tarifa_de(db, tenant_id, comuna)
    if not tarifa:
        raise ErrorEntrega("No hay delivery a esa comuna")
    minimo = monto_minimo_gratis(db, tenant_id)
    if minimo is not None and Decimal(str(monto_productos or 0)) >= minimo:
        return Decimal("0"), tarifa.comuna
    return Decimal(tarifa.costo), tarifa.comuna
