"""Credenciales de pasarela cifradas en la base (change add-pasarelas-pago; portado de EffiCheck D48).

AES-256-GCM con la clave maestra PASARELAS_CLAVE_MAESTRA (32 bytes en base64). El blob es
`version(1) || nonce(12) || texto cifrado + tag`, y el dato asociado ata el blob a su tenant y a su fila
(`tenant:<t>:pasarela:<id>`): copiado a otra fila u otro tenant no se puede descifrar. El texto en claro es el JSON
de los campos del adaptador.
"""
import base64
import hashlib
import json
import logging
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from services.pasarelas import config

log = logging.getLogger(__name__)

VERSION = 1
_avisado = False


class ErrorCifrado(ValueError):
    pass


def decodificar_clave(valor: str | None) -> bytes | None:
    """Clave de 32 bytes desde base64 (estándar o URL-safe); None si falta o no es válida."""
    v = (valor or "").strip()
    if not v:
        return None
    try:
        clave = base64.b64decode(v + "=" * (-len(v) % 4), altchars=b"-_" if ("-" in v or "_" in v) else None)
    except (ValueError, TypeError):
        return None
    return clave if len(clave) == 32 else None


def clave_maestra() -> bytes:
    """Clave vigente. En producción es obligatoria; en desarrollo, si falta, se deriva de SECRET_KEY."""
    global _avisado
    clave = decodificar_clave(config.clave_maestra_env())
    if clave:
        return clave
    if config.es_produccion():
        raise ErrorCifrado("PASARELAS_CLAVE_MAESTRA no está configurada en el servidor (obligatoria en producción)")
    if not _avisado:
        log.warning("PASARELAS_CLAVE_MAESTRA no está definida: se usa una clave derivada (solo desarrollo)")
        _avisado = True
    return hashlib.sha256(f"pasarelas:{config.secreto_desarrollo()}".encode()).digest()


def _asociado(tenant_id: int, id_: int) -> bytes:
    return f"tenant:{tenant_id}:pasarela:{id_}".encode()


def cifrar(datos: dict, tenant_id: int, id_: int, clave: bytes | None = None) -> bytes:
    nonce = os.urandom(12)
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).encode()
    return bytes([VERSION]) + nonce + AESGCM(clave or clave_maestra()).encrypt(nonce, texto, _asociado(tenant_id, id_))


def descifrar(blob: bytes | memoryview | None, tenant_id: int, id_: int, clave: bytes | None = None) -> dict:
    if not blob:
        return {}
    b = bytes(blob)
    if len(b) < 1 + 12 + 16 or b[0] != VERSION:
        raise ErrorCifrado("Credenciales con formato desconocido")
    try:
        texto = AESGCM(clave or clave_maestra()).decrypt(b[1:13], b[13:], _asociado(tenant_id, id_))
    except InvalidTag as e:
        raise ErrorCifrado("No se pudieron descifrar las credenciales (clave maestra distinta o blob de otra pasarela)") from e
    return json.loads(texto)
