"""Configuración de las pasarelas de pago (change add-pasarelas-pago).

- ENTORNO: `desarrollo` habilita la pasarela simulada y las de ambiente INTEGRACION. Cualquier otro valor (o ausente)
  se trata como producción: es el valor seguro por defecto.
- PASARELAS_CLAVE_MAESTRA: 32 bytes en base64 para cifrar credenciales (obligatoria en producción).
- URL_PUBLICA_PAGOS: solo desarrollo; base pública (túnel https) para que el proveedor notifique a la máquina local.
- JWT/SECRET_KEY: en desarrollo, si falta la clave maestra, se deriva una de SECRET_KEY.
"""
import os


def entorno() -> str:
    return (os.getenv("ENTORNO") or "produccion").strip().lower()


def es_produccion() -> bool:
    return entorno() != "desarrollo"


def clave_maestra_env() -> str | None:
    return os.getenv("PASARELAS_CLAVE_MAESTRA")


def secreto_desarrollo() -> str:
    return os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "fme-desarrollo"


def url_publica_pagos() -> str | None:
    v = (os.getenv("URL_PUBLICA_PAGOS") or "").strip().rstrip("/")
    return v or None
