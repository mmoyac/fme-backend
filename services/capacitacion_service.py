"""Catálogo de lecciones del Centro de Capacitación (change add-centro-capacitacion).

Las lecciones son HTML autocontenidos en `capacitacion/<modulo>/`, declarados en el
`manifest.json` de cada módulo. Nunca se arma una ruta con lo que llega en la URL: el archivo
solo se resuelve desde el manifiesto ya validado (D2 del design).
"""
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from utils.modulos import MODULOS

logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent.parent / "capacitacion"
GENERAL = "general"
NOMBRE_GENERAL = "General"
PATRON_SLUG = re.compile(r"^[a-z0-9_-]+$")
LIMITE_BYTES = 2 * 1024 * 1024


def modulos_conocidos() -> list[str]:
    """`general` primero y luego los módulos en el orden de MODULOS."""
    return [GENERAL, *MODULOS.keys()]


def _nombre(modulo: str) -> str:
    return NOMBRE_GENERAL if modulo == GENERAL else MODULOS.get(modulo, modulo)


def cargar_manifiesto(raiz: Path, modulo: str) -> Optional[list[dict]]:
    """Lecciones válidas del módulo, o None si no hay manifiesto o es inválido."""
    carpeta = (raiz / modulo).resolve()
    archivo_manifest = carpeta / "manifest.json"
    if not archivo_manifest.is_file():
        return None
    try:
        datos = json.loads(archivo_manifest.read_text(encoding="utf-8"))
        lecciones = datos["lecciones"]
        if not isinstance(lecciones, list):
            raise ValueError("'lecciones' debe ser una lista")
        validas: list[dict] = []
        vistos: set[str] = set()
        for item in lecciones:
            slug = item["slug"]
            if not isinstance(slug, str) or not PATRON_SLUG.match(slug):
                raise ValueError(f"slug inválido: {slug!r}")
            if slug in vistos:
                raise ValueError(f"slug duplicado: {slug}")
            vistos.add(slug)
            ruta = (carpeta / item["archivo"]).resolve()
            if carpeta not in ruta.parents:
                raise ValueError(f"archivo fuera de la carpeta del módulo: {item['archivo']}")
            if not ruta.is_file():
                raise ValueError(f"archivo inexistente: {item['archivo']}")
            if ruta.stat().st_size > LIMITE_BYTES:
                logger.warning("Capacitación %s/%s pesa más de 2 MB", modulo, slug)
            validas.append({
                "slug": slug,
                "titulo": str(item["titulo"]),
                "descripcion": str(item.get("descripcion", "")),
                "ruta": ruta,
            })
        return validas
    except Exception as exc:  # manifiesto roto: se omite la sección sin botar la API
        logger.error("Manifiesto de capacitación inválido en '%s': %s", modulo, exc)
        return None


def cargar_catalogo(raiz: Path) -> dict[str, list[dict]]:
    catalogo: dict[str, list[dict]] = {}
    for modulo in modulos_conocidos():
        lecciones = cargar_manifiesto(raiz, modulo)
        if lecciones:
            catalogo[modulo] = lecciones
    return catalogo


@lru_cache(maxsize=1)
def catalogo() -> dict[str, list[dict]]:
    return cargar_catalogo(RAIZ)


def secciones_visibles(modulos: Optional[set[str]], cat: Optional[dict] = None) -> list[dict]:
    """Secciones del índice. `modulos=None` = superadmin en modo plataforma (ve todo)."""
    cat = catalogo() if cat is None else cat
    secciones = []
    for modulo in modulos_conocidos():
        if modulo not in cat:
            continue
        if modulos is not None and modulo != GENERAL and modulo not in modulos:
            continue
        secciones.append({
            "modulo": modulo,
            "nombre": _nombre(modulo),
            "lecciones": [
                {"slug": l["slug"], "titulo": l["titulo"], "descripcion": l["descripcion"]}
                for l in cat[modulo]
            ],
        })
    return secciones


def es_modulo_conocido(modulo: str) -> bool:
    return modulo == GENERAL or modulo in MODULOS


def leer_leccion(modulo: str, slug: str, cat: Optional[dict] = None) -> Optional[str]:
    """HTML de la lección, o None si el módulo/slug no es válido o no está declarado."""
    if not es_modulo_conocido(modulo) or not PATRON_SLUG.match(slug or ""):
        return None
    cat = catalogo() if cat is None else cat
    for leccion in cat.get(modulo, []):
        if leccion["slug"] == slug:
            return leccion["ruta"].read_text(encoding="utf-8")
    return None
