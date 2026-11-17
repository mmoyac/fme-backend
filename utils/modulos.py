"""Módulos contratables por tenant (change add-modulos-tenant, modelo de EffiCoop).

El núcleo (dashboard, productos, clientes, precios, locales, usuarios/roles, mantenedores
generales, alertas) está siempre disponible y no figura aquí. Lo demás se contrata por tenant
desde la consola de plataforma y se registra en la tabla `tenant_modulos`.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.database import get_db

NUCLEO = "nucleo"

# Orden = orden de presentación en la consola.
MODULOS: dict[str, str] = {
    "ventas": "Ventas",
    "cotizaciones": "Cotizaciones",
    "preventa": "Pre-venta de cajas",
    "tienda_online": "Tienda online",
    "inventario": "Inventario",
    "compras": "Compras",
    "produccion": "Producción",
    "etiquetado": "Etiquetado nutricional",
    "despacho": "Despacho",
    "cobranza": "Cobranza",
    "comisiones": "Comisiones",
    "fidelizacion": "Fidelización",
}

REQUIERE: dict[str, frozenset[str]] = {
    "cotizaciones": frozenset({"ventas"}),
    "preventa": frozenset({"ventas"}),
    "tienda_online": frozenset({"ventas"}),
    "compras": frozenset({"inventario"}),
    "produccion": frozenset({"inventario"}),
    "etiquetado": frozenset({"produccion"}),
    "despacho": frozenset({"ventas"}),
    "cobranza": frozenset({"ventas"}),
    "comisiones": frozenset({"ventas"}),
    "fidelizacion": frozenset({"ventas"}),
}

# Módulo de cada ítem de menú, por href (ausente = núcleo).
MODULO_POR_HREF: dict[str, str] = {
    "/admin/solicitudes": "ventas",
    "/admin/pedidos": "ventas",
    "/admin/pedidos/pos": "ventas",
    "/admin/cotizaciones": "cotizaciones",
    "/admin/pedidos/cajas": "preventa",
    "/admin/inventario": "inventario",
    "/admin/compras": "compras",
    "/admin/facturas": "compras",
    "/admin/recepcion": "compras",
    "/admin/produccion": "produccion",
    "/admin/produccion/ordenes-trabajo": "produccion",
    "/admin/despacho": "despacho",
    "/admin/cobranza": "cobranza",
    "/admin/notas-credito": "cobranza",
    "/admin/comisiones": "comisiones",
}


def validar_modulos(modulos: set[str]) -> Optional[str]:
    """Devuelve un mensaje de error si el conjunto no es válido, o None si lo es."""
    desconocidos = sorted(m for m in modulos if m not in MODULOS)
    if desconocidos:
        return f"Módulos desconocidos: {', '.join(desconocidos)}"
    for modulo in MODULOS:  # orden estable para mensajes deterministas
        if modulo not in modulos:
            continue
        faltan = sorted(REQUIERE.get(modulo, frozenset()) - modulos)
        if faltan:
            return (
                f"El módulo '{modulo}' requiere: {', '.join(faltan)}"
            )
    return None


def validar_cambio(actuales: set[str], nuevos: set[str]) -> Optional[str]:
    """Como validar_modulos, pero explica mejor el caso de quitar un módulo del que otro depende."""
    quitados = actuales - nuevos
    for modulo in MODULOS:
        if modulo not in nuevos:
            continue
        bloqueantes = sorted(REQUIERE.get(modulo, frozenset()) & quitados)
        if bloqueantes:
            return f"No se puede quitar {', '.join(bloqueantes)}: el módulo '{modulo}' depende de él"
    return validar_modulos(nuevos)


def modulos_de_tenant(db: Session, tenant_id: Optional[int]) -> set[str]:
    if not tenant_id:
        return set()
    from database.models import TenantModulo

    filas = db.query(TenantModulo.modulo).filter(TenantModulo.tenant_id == tenant_id).all()
    return {f[0] for f in filas}


def error_modulo_no_contratado(modulo: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "modulo_no_contratado",
            "modulo": modulo,
            "mensaje": f"Tu plan no incluye el módulo {MODULOS.get(modulo, modulo)}",
        },
    )


def tenant_de_request(request: Request, db: Session) -> Optional[int]:
    """Tenant de la request: token (respeta el contexto de superadmin), API Key o host."""
    from utils.security import SECRET_KEY, ALGORITHM

    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        try:
            payload = jwt.decode(auth[7:].strip(), SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            payload = None
        if payload:
            if payload.get("tenant_id"):
                return int(payload["tenant_id"])
            from database.models import User

            user = db.query(User).filter(User.email == payload.get("sub")).first()
            if user and not payload.get("is_superadmin"):
                return user.tenant_id
            # superadmin sin contexto de tenant: modo plataforma, no aplica módulo
            return None

    from services import tenant_service

    try:
        tenant = tenant_service.get_tenant_from_request(request, db)
    except HTTPException:
        return None  # dominio no registrado: que lo resuelva el endpoint como hoy
    return tenant.id if tenant else None


_tenant_de_request = tenant_de_request  # alias por compatibilidad


def require_modulo(modulo: str):
    """Dependencia FastAPI (síncrona): 403 si el tenant de la request no tiene el módulo.

    No valida autenticación: eso lo sigue haciendo cada endpoint. Solo decide, para el tenant
    de la request, si el módulo está contratado.
    """
    if modulo not in MODULOS:
        raise ValueError(f"Módulo desconocido: {modulo}")

    def dependencia(request: Request, db: Session = Depends(get_db)) -> None:
        tenant_id = tenant_de_request(request, db)
        if tenant_id is None:
            return  # sin tenant (superadmin en modo plataforma o request inválida: la rechaza el endpoint)
        if modulo not in modulos_de_tenant(db, tenant_id):
            raise error_modulo_no_contratado(modulo)

    dependencia.__name__ = f"require_modulo_{modulo}"
    return dependencia
