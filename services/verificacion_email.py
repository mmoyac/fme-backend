"""Verificación del correo del cliente anónimo de la tienda con un código de 6 dígitos (change add-pasarelas-pago).

- `enviar_codigo`: genera el código (se guarda solo su HMAC), vence en 10 min, anula los anteriores y lo envía por
  n8n (webhook `verificacion-email`). Límites: 1 envío por minuto y 5 por hora por correo y tenant.
- `confirmar_codigo`: máximo 5 intentos por código; si es correcto entrega un token firmado (HMAC) válido 30 días que
  liga tenant + correo. La landing lo guarda en el navegador para no pedir el código otra vez en ese dispositivo.
- `token_valido`: lo usa `POST /api/pedidos/` para exigir el correo verificado.
En desarrollo (ENTORNO=desarrollo) el código también se escribe en el log, para probar sin n8n.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from database.models import Tenant, VerificacionEmail
from services.pasarelas import config

log = logging.getLogger(__name__)

N8N_WEBHOOK_VERIFICACION_EMAIL = os.getenv(
    "N8N_WEBHOOK_VERIFICACION_EMAIL", "https://n8n.effi4tech.cl/webhook/verificacion-email")
MINUTOS_CODIGO = 10
MAX_INTENTOS = 5
ESPERA_REENVIO_S = 60
MAX_ENVIOS_HORA = 5
DIAS_TOKEN = 30


class ErrorVerificacion(ValueError):
    pass


def _secreto() -> bytes:
    base = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "fme-desarrollo"
    return hashlib.sha256(f"verificacion-email:{base}".encode()).digest()


def _hash_codigo(tenant_id: int, email: str, codigo: str) -> str:
    return hmac.new(_secreto(), f"{tenant_id}:{email}:{codigo}".encode(), hashlib.sha256).hexdigest()


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def normalizar(email: str) -> str:
    return (email or "").strip().lower()


# ----------------------------------------------------------------------------- token
def emitir_token(tenant_id: int, email: str) -> str:
    cuerpo = base64.urlsafe_b64encode(json.dumps(
        {"t": tenant_id, "e": normalizar(email), "x": int(time.time()) + DIAS_TOKEN * 86400},
        separators=(",", ":")).encode()).decode().rstrip("=")
    firma = hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()
    return f"{cuerpo}.{firma}"


def token_valido(token: str | None, tenant_id: int, email: str) -> bool:
    try:
        cuerpo, firma = (token or "").split(".", 1)
        if not hmac.compare_digest(firma, hmac.new(_secreto(), cuerpo.encode(), hashlib.sha256).hexdigest()):
            return False
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
        return datos["t"] == tenant_id and datos["e"] == normalizar(email) and datos["x"] > time.time()
    except (ValueError, KeyError, TypeError):
        return False


# ----------------------------------------------------------------------------- envío
def _post(payload: dict) -> None:
    try:
        with httpx.Client(timeout=10) as c:
            r = c.post(N8N_WEBHOOK_VERIFICACION_EMAIL, json=payload)
            if r.status_code >= 400:
                log.warning("Webhook verificacion-email respondió %s", r.status_code)
    except Exception as e:   # noqa: BLE001
        log.warning("Webhook verificacion-email falló: %s", e)


def enviar_codigo(db: Session, tenant_id: int, email: str, ip: str | None) -> dict:
    email = normalizar(email)
    ahora = _ahora()
    recientes = (db.query(VerificacionEmail)
                 .filter(VerificacionEmail.tenant_id == tenant_id, VerificacionEmail.email == email,
                         VerificacionEmail.created_at > ahora - timedelta(hours=1))
                 .order_by(VerificacionEmail.created_at.desc()).all())
    if recientes and (ahora - recientes[0].created_at).total_seconds() < ESPERA_REENVIO_S:
        espera = ESPERA_REENVIO_S - int((ahora - recientes[0].created_at).total_seconds())
        raise ErrorVerificacion(f"Espera {espera} segundos para pedir otro código")
    if len(recientes) >= MAX_ENVIOS_HORA:
        raise ErrorVerificacion("Pediste demasiados códigos. Intenta nuevamente en una hora.")
    for v in recientes:
        if not v.verificado_en:
            v.anulado = True
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    db.add(VerificacionEmail(tenant_id=tenant_id, email=email, codigo_hash=_hash_codigo(tenant_id, email, codigo),
                             expira_en=ahora + timedelta(minutes=MINUTOS_CODIGO), ip=(ip or "")[:64]))
    db.commit()
    tenant = db.get(Tenant, tenant_id)
    payload = {"email": email, "codigo": codigo, "minutos": MINUTOS_CODIGO,
               "tienda": tenant.nombre if tenant else "",
               "tienda_url": f"https://{tenant.dominio_principal}" if tenant and tenant.dominio_principal else None}
    if not config.es_produccion():
        log.warning("🔐 [DESARROLLO] Código de verificación para %s: %s", email, codigo)
    threading.Thread(target=_post, args=(payload,), daemon=True).start()
    return {"enviado": True, "minutos": MINUTOS_CODIGO, "reenviar_en": ESPERA_REENVIO_S}


def confirmar_codigo(db: Session, tenant_id: int, email: str, codigo: str) -> dict:
    email = normalizar(email)
    codigo = (codigo or "").strip()
    v = (db.query(VerificacionEmail)
         .filter(VerificacionEmail.tenant_id == tenant_id, VerificacionEmail.email == email,
                 VerificacionEmail.anulado.is_(False), VerificacionEmail.verificado_en.is_(None))
         .order_by(VerificacionEmail.created_at.desc()).with_for_update().first())
    if not v or v.expira_en <= _ahora():
        raise ErrorVerificacion("El código expiró o no existe. Pide uno nuevo.")
    if v.intentos >= MAX_INTENTOS:
        raise ErrorVerificacion("Superaste los intentos permitidos. Pide un código nuevo.")
    v.intentos += 1
    if not (codigo.isdigit() and len(codigo) == 6
            and hmac.compare_digest(v.codigo_hash, _hash_codigo(tenant_id, email, codigo))):
        restantes = MAX_INTENTOS - v.intentos
        if restantes <= 0:
            v.anulado = True
        db.commit()
        raise ErrorVerificacion("Código incorrecto." + (f" Te quedan {restantes} intentos." if restantes > 0
                                                         else " Pide un código nuevo."))
    v.verificado_en = _ahora()
    db.commit()
    return {"verificado": True, "token": emitir_token(tenant_id, email), "dias": DIAS_TOKEN}
