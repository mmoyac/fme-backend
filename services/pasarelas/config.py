"""Configuración de las pasarelas de pago (change add-pasarelas-pago).

- ENTORNO: `desarrollo` habilita la pasarela simulada y las de ambiente INTEGRACION. Cualquier otro valor (o ausente)
  se trata como producción: es el valor seguro por defecto.
- PASARELAS_CLAVE_MAESTRA: 32 bytes en base64 para cifrar credenciales (obligatoria en producción).
- PASARELAS_CLAVE_DEMO: opcional (add-delivery-por-comuna). Si está definida, quien presente esa clave (landing con
  `?demo=<clave>`) ve también las pasarelas de ambiente INTEGRACION en producción; nunca la Simulada.
- URL_PUBLICA_PAGOS: solo desarrollo; base pública (túnel https) para que el proveedor notifique a la máquina local.
- JWT/SECRET_KEY: en desarrollo, si falta la clave maestra, se deriva una de SECRET_KEY.
"""
import hmac
import os


def entorno() -> str:
    return (os.getenv("ENTORNO") or "produccion").strip().lower()


def es_produccion() -> bool:
    return entorno() != "desarrollo"


def clave_maestra_env() -> str | None:
    return os.getenv("PASARELAS_CLAVE_MAESTRA")


def secreto_desarrollo() -> str:
    return os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "fme-desarrollo"


def es_demo(clave: str | None) -> bool:
    """True si `clave` coincide con PASARELAS_CLAVE_DEMO (comparación en tiempo constante). Sin clave configurada: False."""
    esperada = (os.getenv("PASARELAS_CLAVE_DEMO") or "").strip()
    if not esperada or not clave:
        return False
    return hmac.compare_digest(clave.strip().encode(), esperada.encode())


def url_publica_pagos() -> str | None:
    v = (os.getenv("URL_PUBLICA_PAGOS") or "").strip().rstrip("/")
    return v or None
