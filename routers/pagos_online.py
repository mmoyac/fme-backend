"""Pagos en línea con pasarelas (change add-pasarelas-pago).

Públicos (landing, sin sesión):
- GET  /api/pagos/opciones                → pasarelas que pueden cobrar en este tenant (tenant por dominio)
- POST /api/pagos                         → crea la intención de un pedido y devuelve la redirección al proveedor
- GET  /api/pagos/{id}                    → estado de la intención (pantalla de resultado)
- POST /api/pagos/{id}/consultar          → consulta al proveedor (máx. 1 cada 10 s por intención)
- POST /api/pagos/{id}/simulada           → resultado de la pasarela simulada (solo desarrollo)
- GET|POST /api/pagos/retorno/{proveedor} → el navegador vuelve del proveedor (303 a la landing)
- POST /api/pagos/webhook/{proveedor}     → notificación servidor a servidor del proveedor
Retorno y notificación llevan `?tenant=<id>` (los arma el backend) y solo IDENTIFICAN la transacción: el resultado
se consulta siempre al proveedor. Un token desconocido no genera llamadas al proveedor.

Administración (rol admin, tenant del usuario): /api/admin/pasarelas
"""
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from database.database import get_db
from database.models import PagoOnline, PasarelaPago, Pedido, Tenant
from services import pagos_online as pagos
from services.pasarelas import adaptador_de, cifrado, codigos_disponibles, config
from services.pasarelas.base import ErrorPasarela
from services.tenant_service import get_tenant_from_request
from utils.permisos import ROLES_ADMIN, require_roles

log = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()

# ----------------------------------------------------------------------------- límite por IP
LIMITE_POR_MINUTO = 30
_ventanas: dict[str, deque] = defaultdict(deque)
_candado = threading.Lock()


def limitar(request: Request) -> None:
    """Límite simple por IP (en memoria del proceso): frena el abuso con tokens inventados."""
    ip = (request.headers.get("x-real-ip") or (request.client.host if request.client else "?")).strip()
    ahora = time.monotonic()
    with _candado:
        v = _ventanas[ip]
        while v and ahora - v[0] > 60:
            v.popleft()
        if len(v) >= LIMITE_POR_MINUTO:
            raise HTTPException(429, "Demasiadas solicitudes; intente en un minuto")
        v.append(ahora)


# ----------------------------------------------------------------------------- URLs
def _base_api(request: Request) -> str:
    import os
    fija = (os.getenv("URL_API_PUBLICA") or "").strip().rstrip("/")
    if fija:
        return fija
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "http").split(",")[0].strip()
    host = request.headers.get("host") or request.url.netloc
    if config.es_produccion() and not host.startswith(("localhost", "127.0.0.1")):
        proto = "https"
    return f"{proto}://{host}"


def _url_sitio(request: Request, tenant: Tenant) -> str:
    """Origen de la landing a la que vuelve el cliente. Solo se acepta el Origin si coincide con el dominio con que se
    detectó el tenant (o es local en desarrollo); si no, el dominio principal del tenant."""
    origen = (request.headers.get("origin") or "").rstrip("/")
    host_tenant = (request.headers.get("x-forwarded-host") or "").split(":")[0].lower()
    if origen:
        h = (urlparse(origen).hostname or "").lower()
        locales = ("localhost", "127.0.0.1")
        if h and (h == host_tenant or h == (tenant.dominio_principal or "").lower()
                  or h == f"www.{(tenant.dominio_principal or '').lower()}"
                  or (not config.es_produccion() and (h in locales or h.endswith(".local") or h.endswith(".localhost")))):
            return origen
    return f"https://{tenant.dominio_principal}" if tenant.dominio_principal else "http://localhost:3000"


def _tenant_publico(request: Request, db: Session) -> Tenant:
    tenant = get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(404, "Tienda no encontrada")
    return tenant


def _error(e: pagos.ErrorPago) -> HTTPException:
    return HTTPException(404 if isinstance(e, pagos.ErrorNoEncontrado) else 400, str(e))


# ----------------------------------------------------------------------------- checkout (público)
@router.get("/opciones")
def opciones(request: Request, db: Session = Depends(get_db)):
    tenant = _tenant_publico(request, db)
    return {"pasarelas": pagos.pasarelas_disponibles(db, tenant.id)}


class CrearPago(BaseModel):
    pedido_id: int
    token_seguimiento: str = Field(min_length=10, max_length=128)
    pasarela_id: int | None = None
    email: str | None = Field(default=None, max_length=255)


@router.post("")
def crear_pago(datos: CrearPago, request: Request, db: Session = Depends(get_db)):
    limitar(request)
    tenant = _tenant_publico(request, db)
    try:
        r = pagos.crear_intencion(db, tenant.id, datos.pedido_id, datos.token_seguimiento, datos.pasarela_id,
                                  datos.email, _url_sitio(request, tenant))
    except pagos.ErrorPago as e:
        db.rollback()
        raise _error(e)
    except cifrado.ErrorCifrado as e:
        db.rollback()
        log.error("Pasarelas: %s", e)
        raise HTTPException(503, "El pago en línea no está disponible en este momento")
    if r.get("reutilizada"):
        return {"id": r["id"], "url": r["url_pago"], "metodo": "GET", "campos": {}}
    base = _base_api(request)
    try:
        red = pagos.iniciar_en_proveedor(tenant.id, r["id"], {
            "api": base, "notificacion": config.url_publica_pagos() or base, "sitio": _url_sitio(request, tenant)})
    except pagos.ErrorPago as e:
        raise HTTPException(502, str(e))
    except cifrado.ErrorCifrado as e:
        log.error("Pasarelas: %s", e)
        raise HTTPException(503, "El pago en línea no está disponible en este momento")
    return {"id": r["id"], "url": red.url, "metodo": red.metodo, "campos": dict(red.campos)}


@router.get("/{pago_id}")
def estado_pago(pago_id: str, db: Session = Depends(get_db)):
    if not pagos._id_intencion(pago_id):
        raise HTTPException(404, "Pago no encontrado")
    e = pagos.estado_publico(db, pago_id)
    if not e:
        raise HTTPException(404, "Pago no encontrado")
    return e


@router.post("/{pago_id}/consultar")
def consultar_pago(pago_id: str, request: Request, db: Session = Depends(get_db)):
    limitar(request)
    if not pagos._id_intencion(pago_id):
        raise HTTPException(404, "Pago no encontrado")
    try:
        pagos.consultar_ahora(pago_id)
    except cifrado.ErrorCifrado as e:
        log.error("Pasarelas: %s", e)
    db.expire_all()
    e = pagos.estado_publico(db, pago_id)
    if not e:
        raise HTTPException(404, "Pago no encontrado")
    return e


class ResultadoSimulado(BaseModel):
    aprobado: bool


@router.post("/{pago_id}/simulada")
def pagar_simulada(pago_id: str, datos: ResultadoSimulado, request: Request, db: Session = Depends(get_db)):
    if config.es_produccion():
        raise HTTPException(404, "No disponible")
    tenant = _tenant_publico(request, db)
    if not pagos._id_intencion(pago_id):
        raise HTTPException(404, "Pago no encontrado")
    try:
        return pagos.confirmar_simulada(tenant.id, pago_id, datos.aprobado)
    except pagos.ErrorPago as e:
        raise _error(e)


# ----------------------------------------------------------------------------- retorno y notificación (público)
async def _datos(request: Request) -> dict:
    """Parámetros de la URL más el cuerpo: formulario (Flow) o JSON (Khipu, Mercado Pago; solo escalares)."""
    datos = dict(request.query_params)
    if request.method == "POST":
        try:
            if "json" in request.headers.get("content-type", ""):
                cuerpo = await request.json()
                if isinstance(cuerpo, dict):
                    datos.update({k: str(v) for k, v in cuerpo.items() if isinstance(v, (str, int, float, bool))
                                  and k not in ("tenant", "intencion")})
            else:
                datos.update({k: str(v) for k, v in (await request.form()).items() if k not in ("tenant", "intencion")})
        except Exception:   # noqa: BLE001  cuerpo ilegible: se ignora (solo identifica, nunca prueba un pago)
            pass
    return datos


def _tenant_de_param(datos: dict) -> int | None:
    try:
        return int(datos.get("tenant") or 0) or None
    except ValueError:
        return None


def _destino_retorno(tenant_id: int | None, pago_id: str | None) -> str:
    with pagos.abrir_sesion() as db:
        sitio = None
        if pago_id:
            sitio = db.query(PagoOnline.url_sitio).filter(PagoOnline.id == pago_id).scalar()
        if not sitio and tenant_id:
            t = db.get(Tenant, tenant_id)
            sitio = f"https://{t.dominio_principal}" if t and t.dominio_principal else None
    sitio = sitio or "/"
    return f"{sitio.rstrip('/')}/checkout/resultado" + (f"?pago={pago_id}" if pago_id else "")


@router.api_route("/retorno/{proveedor}", methods=["GET", "POST"])
async def retorno(proveedor: str, request: Request):
    """El cliente vuelve del proveedor: se verifica el pago y se lo lleva a la pantalla de resultado de la landing."""
    limitar(request)
    datos = await _datos(request)
    tenant_id = _tenant_de_param(datos)
    pago_id = None
    if tenant_id:
        try:
            pago_id = await run_in_threadpool(pagos.procesar_aviso, tenant_id, proveedor.upper(), datos)
        except Exception:   # noqa: BLE001  el cliente siempre debe llegar a la pantalla de resultado
            log.exception("Error procesando el retorno de %s", proveedor)
    destino = await run_in_threadpool(_destino_retorno, tenant_id, pago_id)
    return RedirectResponse(destino, status_code=303)


@router.post("/webhook/{proveedor}")
async def notificacion(proveedor: str, request: Request):
    """Notificación servidor a servidor. Responde 200 si la intención existe (aunque el proveedor no responda: la
    conciliación lo resolverá) y 404 si no."""
    limitar(request)
    datos = await _datos(request)
    tenant_id = _tenant_de_param(datos)
    if not tenant_id:
        return JSONResponse({"detail": "Transacción no encontrada"}, status_code=404)
    pago_id = await run_in_threadpool(pagos.procesar_aviso, tenant_id, proveedor.upper(), datos)
    if not pago_id:
        return JSONResponse({"detail": "Transacción no encontrada"}, status_code=404)
    return {"recibido": True}


# ============================================================================= administración
def _vista(p: PasarelaPago) -> dict:
    a = adaptador_de(p.proveedor)
    return {
        "id": p.id, "proveedor": p.proveedor, "nombre_proveedor": a.nombre if a else p.proveedor,
        "nombre_visible": p.nombre_visible, "ambiente": p.ambiente, "orden": p.orden, "activo": p.activo,
        "credenciales_cargadas": bool(p.credenciales_cifradas) or (a is not None and not a.campos_credenciales),
        "credenciales_actualizadas_en": p.credenciales_actualizadas_en,
        "ultima_prueba_en": p.ultima_prueba_en, "ultima_prueba_ok": p.ultima_prueba_ok,
        "ultima_prueba_mensaje": p.ultima_prueba_mensaje,
        "puede_cobrar": pagos.puede_cobrar(p),
    }


def _pasarela_admin(db: Session, user, pasarela_id: int) -> PasarelaPago:
    p = db.query(PasarelaPago).filter(PasarelaPago.id == pasarela_id, PasarelaPago.tenant_id == user.tenant_id).first()
    if not p:
        raise HTTPException(404, "Pasarela no encontrada")
    return p


_rol_admin = require_roles(ROLES_ADMIN)


def admin(user=Depends(_rol_admin)):
    """Admin del tenant, o superadmin operando dentro de un tenant (switch-tenant). En modo plataforma no hay tenant."""
    if not user.tenant_id:
        raise HTTPException(400, "Seleccione un tenant (Superadmin → Operar en tenant) para configurar sus pasarelas de pago")
    return user


@admin_router.get("/proveedores")
def proveedores(user=Depends(admin)):
    salida = []
    for c in codigos_disponibles():
        if c == "SIMULADA" and config.es_produccion():
            continue
        a = adaptador_de(c)
        salida.append({"codigo": c, "nombre": a.nombre, "requiere_email": a.requiere_email,
                       "monto_minimo": a.monto_minimo,
                       "campos": [{"codigo": f.codigo, "etiqueta": f.etiqueta, "secreto": f.secreto}
                                  for f in a.campos_credenciales]})
    return {"proveedores": salida, "entorno": "desarrollo" if not config.es_produccion() else "produccion"}


@admin_router.get("")
def listar(db: Session = Depends(get_db), user=Depends(admin)):
    q = db.query(PasarelaPago).filter(PasarelaPago.tenant_id == user.tenant_id).order_by(PasarelaPago.orden, PasarelaPago.id)
    return [_vista(p) for p in q]


class PasarelaCrear(BaseModel):
    proveedor: str
    nombre_visible: str = Field(min_length=2, max_length=60)
    ambiente: str = "INTEGRACION"
    orden: int = 0


class PasarelaEditar(BaseModel):
    nombre_visible: str | None = Field(default=None, min_length=2, max_length=60)
    ambiente: str | None = None
    orden: int | None = None


def _validar_ambiente(ambiente: str, proveedor: str) -> str:
    a = (ambiente or "").upper()
    if a not in ("INTEGRACION", "PRODUCCION"):
        raise HTTPException(422, "Ambiente inválido (INTEGRACION o PRODUCCION)")
    if proveedor == "SIMULADA" and a != "INTEGRACION":
        raise HTTPException(422, "La pasarela simulada solo existe en ambiente de integración")
    return a


@admin_router.post("", status_code=201)
def crear(datos: PasarelaCrear, db: Session = Depends(get_db), user=Depends(admin)):
    proveedor = datos.proveedor.upper()
    if not adaptador_de(proveedor) or (proveedor == "SIMULADA" and config.es_produccion()):
        raise HTTPException(422, "Proveedor aún no disponible")
    p = PasarelaPago(tenant_id=user.tenant_id, proveedor=proveedor, nombre_visible=datos.nombre_visible.strip(),
                     ambiente=_validar_ambiente(datos.ambiente, proveedor), orden=datos.orden, activo=False)
    db.add(p)
    db.commit()
    db.refresh(p)
    log.info("Pasarela %s (%s) creada por %s", p.id, proveedor, user.email)
    return _vista(p)


@admin_router.patch("/{pasarela_id}")
def editar(pasarela_id: int, datos: PasarelaEditar, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    if datos.nombre_visible is not None:
        p.nombre_visible = datos.nombre_visible.strip()
    if datos.orden is not None:
        p.orden = datos.orden
    if datos.ambiente is not None:
        nuevo = _validar_ambiente(datos.ambiente, p.proveedor)
        if nuevo != p.ambiente:   # cambiar el ambiente desactiva y exige una nueva prueba
            p.ambiente, p.activo, p.ultima_prueba_ok, p.ultima_prueba_en = nuevo, False, None, None
    db.commit()
    db.refresh(p)
    return _vista(p)


@admin_router.put("/{pasarela_id}/credenciales")
def reemplazar_credenciales(pasarela_id: int, datos: dict, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    a = adaptador_de(p.proveedor)
    campos = {f.codigo for f in a.campos_credenciales}
    valores = {k: str(v).strip() for k, v in (datos or {}).items() if k in campos and str(v or "").strip()}
    faltan = [f.etiqueta for f in a.campos_credenciales if f.codigo not in valores]
    if faltan:
        raise HTTPException(422, "Faltan: " + ", ".join(faltan))
    try:
        p.credenciales_cifradas = cifrado.cifrar(valores, p.tenant_id, p.id)
    except cifrado.ErrorCifrado as e:
        raise HTTPException(503, str(e))
    p.credenciales_actualizadas_en = datetime.now(timezone.utc)
    p.activo, p.ultima_prueba_ok = False, None   # credenciales nuevas: hay que probar y activar de nuevo
    db.commit()
    log.info("Credenciales de la pasarela %s reemplazadas por %s", p.id, user.email)   # nunca los valores
    db.refresh(p)
    return _vista(p)


@admin_router.post("/{pasarela_id}/probar")
def probar(pasarela_id: int, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    ok, mensaje = True, "Conexión exitosa"
    try:
        adaptador_de(p.proveedor).probar(pagos.a_pasarela(p))
    except ErrorPasarela as e:
        ok, mensaje = False, e.mensaje
    except cifrado.ErrorCifrado as e:
        ok, mensaje = False, str(e)
    p.ultima_prueba_en, p.ultima_prueba_ok, p.ultima_prueba_mensaje = datetime.now(timezone.utc), ok, mensaje[:300]
    db.commit()
    log.info("Prueba de la pasarela %s por %s: %s", p.id, user.email, "OK" if ok else "falló")
    db.refresh(p)
    return _vista(p)


@admin_router.post("/{pasarela_id}/activar")
def activar(pasarela_id: int, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    if p.proveedor == "SIMULADA" and config.es_produccion():
        raise HTTPException(422, "La pasarela simulada no se puede activar en producción")
    a = adaptador_de(p.proveedor)
    if a.campos_credenciales and not p.credenciales_cifradas:
        raise HTTPException(422, "Cargue las credenciales antes de activar")
    prueba_vigente = p.ultima_prueba_ok and p.ultima_prueba_en and (
        not p.credenciales_actualizadas_en or p.ultima_prueba_en >= p.credenciales_actualizadas_en)
    if p.ambiente == "PRODUCCION" and not prueba_vigente:
        raise HTTPException(422, "Para activar en producción, primero pruebe la conexión con las credenciales actuales")
    p.activo = True
    db.commit()
    db.refresh(p)
    return _vista(p)


@admin_router.post("/{pasarela_id}/desactivar")
def desactivar(pasarela_id: int, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    p.activo = False
    db.commit()
    db.refresh(p)
    return _vista(p)


@admin_router.delete("/{pasarela_id}", status_code=204)
def eliminar(pasarela_id: int, db: Session = Depends(get_db), user=Depends(admin)):
    p = _pasarela_admin(db, user, pasarela_id)
    if db.query(PagoOnline.id).filter(PagoOnline.pasarela_id == p.id).first():
        raise HTTPException(409, "La pasarela tiene pagos registrados: desactívela en lugar de eliminarla")
    db.delete(p)
    db.commit()


@admin_router.get("/pagos/lista")
def listar_pagos(estado: str | None = None, limite: int = 100, db: Session = Depends(get_db), user=Depends(admin)):
    """Pagos en línea del tenant (seguimiento; EN_REVISION requiere acción manual)."""
    q = (db.query(PagoOnline, Pedido.numero_pedido, PasarelaPago.nombre_visible)
         .join(Pedido, Pedido.id == PagoOnline.pedido_id).join(PasarelaPago, PasarelaPago.id == PagoOnline.pasarela_id)
         .filter(PagoOnline.tenant_id == user.tenant_id))
    if estado:
        q = q.filter(PagoOnline.estado == estado.upper())
    filas = q.order_by(PagoOnline.iniciado_en.desc()).limit(min(max(limite, 1), 500)).all()
    return [{"id": str(p.id), "pedido_id": p.pedido_id, "numero_pedido": num, "pasarela": nom, "monto": int(p.monto),
             "estado": p.estado, "iniciado_en": p.iniciado_en, "confirmado_en": p.confirmado_en,
             "id_transaccion": p.id_transaccion_proveedor, "motivo_revision": p.motivo_revision,
             "medio": (p.respuesta_proveedor or {}).get("medio")} for p, num, nom in filas]
