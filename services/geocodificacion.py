"""Verificación de la comuna de una dirección con Mapbox (change add-delivery-por-comuna).

Mapbox (geocoding v5, país Chile) devuelve la comuna en el contexto `place`. Solo se confía en coincidencias de tipo
dirección con relevancia alta: las coincidencias aproximadas suelen caer en otra comuna u otra región.
Sin token, sin red o sin coincidencia confiable, la dirección queda "no verificada" (no se rechaza el pedido por eso).

Variable: MAPBOX_ACCESS_TOKEN (o NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN).
"""
import logging
import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx

log = logging.getLogger(__name__)

URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{q}.json"
RELEVANCIA_MINIMA = 0.9
# Sesgo hacia la Región Metropolitana (Lampa) para direcciones ambiguas
PROXIMIDAD = "-70.876,-33.285"

transporte: httpx.BaseTransport | None = None  # tests


@dataclass(frozen=True)
class Verificacion:
    comuna: str | None       # comuna según Mapbox (None si no hubo coincidencia confiable)
    direccion: str | None    # dirección normalizada por Mapbox


def _token() -> str | None:
    return (os.getenv("MAPBOX_ACCESS_TOKEN") or os.getenv("NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN") or "").strip() or None


def comuna_de_direccion(direccion: str) -> Verificacion:
    """Comuna de la dirección según Mapbox, o Verificacion(None, None) si no se pudo determinar con confianza."""
    token = _token()
    texto = (direccion or "").strip()
    if not token or len(texto) < 5:
        return Verificacion(None, None)
    try:
        with httpx.Client(timeout=6, transport=transporte) as cliente:
            r = cliente.get(URL.format(q=quote(texto, safe="")), params={
                "access_token": token, "country": "cl", "types": "address", "limit": 1, "language": "es",
                "proximity": PROXIMIDAD,
            })
        if r.status_code != 200:
            log.warning("Mapbox respondió %s al verificar una dirección", r.status_code)
            return Verificacion(None, None)
        features = r.json().get("features") or []
    except (httpx.HTTPError, ValueError) as e:
        log.warning("No se pudo verificar la dirección con Mapbox: %s", e)
        return Verificacion(None, None)
    if not features or float(features[0].get("relevance") or 0) < RELEVANCIA_MINIMA:
        return Verificacion(None, None)
    f = features[0]
    comuna = next((c.get("text") for c in f.get("context") or [] if str(c.get("id", "")).startswith("place.")), None)
    return Verificacion(comuna, f.get("place_name"))
