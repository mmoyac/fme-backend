"""Tarifas de delivery por comuna (change add-delivery-por-comuna): normalización y cálculo del costo (sin BD).

Ejecutar en el contenedor:  docker exec fme-backend python -m pytest tests/test_tarifas_delivery.py -q --noconftest
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from services import tarifas_delivery as td

TARIFAS = {"colina": SimpleNamespace(comuna="Colina", costo=Decimal("3000"))}


@pytest.fixture
def tabla(monkeypatch):
    estado = {"minimo": None}
    monkeypatch.setattr(td, "tarifa_de", lambda db, t, comuna: TARIFAS.get(td.normalizar_comuna(comuna)))
    monkeypatch.setattr(td, "monto_minimo_gratis", lambda db, t: estado["minimo"])
    return estado


def test_normalizar_comuna():
    assert td.normalizar_comuna("  Ñuñoa ") == "nunoa"
    assert td.normalizar_comuna("Estación   Central") == "estacion central"
    assert td.normalizar_comuna(None) == ""


def test_retiro_no_cobra(tabla):
    assert td.costo_delivery(None, 1, "retiro", "Colina", 5000) == (Decimal("0"), None)


def test_despacho_con_tarifa(tabla):
    assert td.costo_delivery(None, 1, "DESPACHO", "colina ", 8000) == (Decimal("3000"), "Colina")


def test_envio_gratis_sobre_minimo(tabla):
    tabla["minimo"] = Decimal("30000")
    assert td.costo_delivery(None, 1, "DESPACHO", "Colina", 35000) == (Decimal("0"), "Colina")
    assert td.costo_delivery(None, 1, "DESPACHO", "Colina", 29999) == (Decimal("3000"), "Colina")


def test_comuna_sin_tarifa(tabla):
    with pytest.raises(td.ErrorEntrega, match="No hay delivery"):
        td.costo_delivery(None, 1, "DESPACHO", "Arica", 8000)


def test_modalidad_invalida(tabla):
    with pytest.raises(td.ErrorEntrega, match="Modalidad"):
        td.costo_delivery(None, 1, "", None, 8000)


# ---------------------------------------------------------------- verificación de dirección con Mapbox (sin red)
def _mapbox(features, status=200):
    import httpx
    return httpx.MockTransport(lambda req: httpx.Response(status, json={"features": features}))


def _feature(comuna, relevancia=1.0):
    return {"relevance": relevancia, "place_name": f"Baquedano 1200, {comuna}, Chile",
            "context": [{"id": "postcode.1", "text": "9380000"}, {"id": "place.1", "text": comuna},
                        {"id": "region.1", "text": "Región Metropolitana de Santiago"}]}


def test_mapbox_comuna_confiable(monkeypatch):
    from services import geocodificacion as g
    monkeypatch.setenv("MAPBOX_ACCESS_TOKEN", "pk.prueba")
    monkeypatch.setattr(g, "transporte", _mapbox([_feature("Lampa")]))
    v = g.comuna_de_direccion("Baquedano 1200, Lampa")
    assert v.comuna == "Lampa" and "Baquedano 1200" in v.direccion


def test_mapbox_baja_relevancia_no_verifica(monkeypatch):
    from services import geocodificacion as g
    monkeypatch.setenv("MAPBOX_ACCESS_TOKEN", "pk.prueba")
    monkeypatch.setattr(g, "transporte", _mapbox([_feature("Molina", 0.6)]))
    assert g.comuna_de_direccion("Calle inventada 500").comuna is None


def test_mapbox_sin_token_o_error(monkeypatch):
    from services import geocodificacion as g
    monkeypatch.delenv("MAPBOX_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN", raising=False)
    assert g.comuna_de_direccion("Baquedano 1200, Lampa").comuna is None
    monkeypatch.setenv("MAPBOX_ACCESS_TOKEN", "pk.prueba")
    monkeypatch.setattr(g, "transporte", _mapbox([], status=401))
    assert g.comuna_de_direccion("Baquedano 1200, Lampa").comuna is None
