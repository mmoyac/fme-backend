"""Pasarelas de pago (change add-pasarelas-pago): cifrado y adaptadores con un doble HTTP (sin red ni BD).

Ejecutar en el contenedor:  docker exec fme-backend python -m pytest tests/test_pasarelas.py -q --noconftest
"""
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs

import httpx
import pytest

from services.pasarelas import adaptador_de, cifrado
from services.pasarelas import flow as flow_mod
from services.pasarelas import mercadopago as mp_mod
from services.pasarelas.base import ErrorPasarela, Intencion, Pasarela, Urls

URLS = Urls(retorno="https://api.masasestacion.cl/api/pagos/retorno/x?tenant=1",
            notificacion="https://api.masasestacion.cl/api/pagos/webhook/x?tenant=1",
            portal="https://masasestacion.cl")
URLS_LOCAL = Urls(retorno="http://localhost:8000/api/pagos/retorno/x?tenant=1",
                  notificacion="http://localhost:8000/api/pagos/webhook/x?tenant=1", portal="http://localhost:3000")


def _intencion(**cambios) -> Intencion:
    base = dict(id="7d1c1e0a-0000-4000-8000-000000000001", orden_comercio="PAPRUEBA0000000000000000AB", monto=14600,
                asunto="Pedido ME-2026-00001 Masas Estación", email="cliente@ejemplo.cl",
                expira_en=datetime.now(timezone.utc) + timedelta(minutes=15))
    return Intencion(**{**base, **cambios})


# ---------------------------------------------------------------- registro y cifrado
def test_registro_de_adaptadores():
    for c in ("SIMULADA", "MERCADOPAGO", "FLOW", "KHIPU"):
        assert adaptador_de(c).codigo == c
    assert adaptador_de("mercadopago").codigo == "MERCADOPAGO"
    assert adaptador_de("WEBPAY") is None


def test_cifrado_ida_y_vuelta_y_atado_a_su_fila():
    clave = b"k" * 32
    blob = cifrado.cifrar({"access_token": "APP_USR-123"}, 1, 7, clave=clave)
    assert b"APP_USR" not in blob
    assert cifrado.descifrar(blob, 1, 7, clave=clave) == {"access_token": "APP_USR-123"}
    for t, i, k in ((2, 7, clave), (1, 8, clave), (1, 7, b"z" * 32)):   # otro tenant, otra pasarela, otra clave
        with pytest.raises(cifrado.ErrorCifrado):
            cifrado.descifrar(blob, t, i, clave=k)


def test_clave_obligatoria_en_produccion(monkeypatch):
    monkeypatch.delenv("PASARELAS_CLAVE_MAESTRA", raising=False)
    monkeypatch.setenv("ENTORNO", "produccion")
    with pytest.raises(cifrado.ErrorCifrado):
        cifrado.clave_maestra()
    monkeypatch.setenv("ENTORNO", "desarrollo")
    assert len(cifrado.clave_maestra()) == 32


def test_simulada_bloqueada_fuera_de_desarrollo(monkeypatch):
    p = Pasarela(id=1, tenant_id=1, proveedor="SIMULADA", ambiente="INTEGRACION", nombre_visible="Prueba")
    monkeypatch.setenv("ENTORNO", "produccion")
    with pytest.raises(ErrorPasarela):
        adaptador_de("SIMULADA").crear(p, _intencion(), URLS)
    monkeypatch.setenv("ENTORNO", "desarrollo")
    r = adaptador_de("SIMULADA").crear(p, _intencion(), URLS)
    assert r.url == "https://masasestacion.cl/checkout/simulada?pago=7d1c1e0a-0000-4000-8000-000000000001"


# ---------------------------------------------------------------- Flow (portado de EffiCheck)
PASARELA_FLOW = Pasarela(id=1, tenant_id=1, proveedor="FLOW", ambiente="INTEGRACION", nombre_visible="Flow",
                         credenciales={"api_key": "AK-1", "secret_key": "secreto-de-prueba"})


@pytest.fixture
def doble_flow(monkeypatch):
    estado = {"llamadas": [], "respuestas": {}}

    def manejar(req: httpx.Request) -> httpx.Response:
        servicio = req.url.path.split("/api/", 1)[1]
        params = (dict(req.url.params) if req.method == "GET"
                  else {k: v[0] for k, v in parse_qs(req.content.decode()).items()})
        estado["llamadas"].append({"metodo": req.method, "host": req.url.host, "servicio": servicio, "params": params})
        status, cuerpo = estado["respuestas"].get(servicio, (500, None))
        return httpx.Response(status, json=cuerpo) if cuerpo is not None else httpx.Response(status, text="error")

    monkeypatch.setattr(flow_mod, "transporte", httpx.MockTransport(manejar))
    return estado


def test_flow_firma_contra_vector():
    params = {"currency": "CLP", "apiKey": "XXXX-XXXX-XXXX", "amount": 5000, "s": "se-ignora"}
    assert flow_mod.firmar(params, "secreto-de-prueba") == "23a2e1765aa31ff2e0e242d8eb5650ae3302d8089159c3a5c968faa14b3578c8"


def test_flow_crear_y_verificar(doble_flow):
    doble_flow["respuestas"]["payment/create"] = (200, {"url": "https://sandbox.flow.cl/app/web/pay.php", "token": "TK1",
                                                        "flowOrder": 99})
    r = adaptador_de("FLOW").crear(PASARELA_FLOW, _intencion(), URLS)
    assert r.url.endswith("?token=TK1") and doble_flow["llamadas"][0]["host"] == "sandbox.flow.cl"
    assert doble_flow["llamadas"][0]["params"]["amount"] == "14600"
    doble_flow["respuestas"]["payment/getStatusExtended"] = (200, {"flowOrder": 99, "commerceOrder": "PAPRUEBA0000000000000000AB",
                                                                   "status": 2, "amount": 14600, "paymentData": {"media": "Webpay"}})
    v = adaptador_de("FLOW").verificar(PASARELA_FLOW, "TK1")
    assert (v.estado, v.monto, v.id_transaccion) == ("APROBADO", 14600, "99")


def test_flow_probar_distingue_credenciales(doble_flow):
    doble_flow["respuestas"]["payment/getStatusByCommerceId"] = (400, {"code": 1700, "message": "Transaction not found"})
    adaptador_de("FLOW").probar(PASARELA_FLOW)
    doble_flow["respuestas"]["payment/getStatusByCommerceId"] = (400, {"code": 501, "message": "apiKey not found"})
    with pytest.raises(ErrorPasarela) as e:
        adaptador_de("FLOW").probar(PASARELA_FLOW)
    assert e.value.credenciales


# ---------------------------------------------------------------- Mercado Pago
PASARELA_MP = Pasarela(id=2, tenant_id=1, proveedor="MERCADOPAGO", ambiente="INTEGRACION", nombre_visible="Mercado Pago",
                       credenciales={"access_token": "TEST-123"})


@pytest.fixture
def doble_mp(monkeypatch):
    estado = {"llamadas": [], "respuestas": {}}

    def manejar(req: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(req.content) if req.content else None
        estado["llamadas"].append({"metodo": req.method, "ruta": req.url.path, "params": dict(req.url.params),
                                   "headers": dict(req.headers), "cuerpo": cuerpo})
        status, resp = estado["respuestas"].get(req.url.path, (500, None))
        return httpx.Response(status, json=resp) if resp is not None else httpx.Response(status, text="error")

    monkeypatch.setattr(mp_mod, "transporte", httpx.MockTransport(manejar))
    return estado


def test_mp_crear_preferencia_con_monto_del_backend(doble_mp):
    doble_mp["respuestas"]["/checkout/preferences"] = (201, {"id": "PREF-1", "init_point": "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=PREF-1"})
    r = adaptador_de("MERCADOPAGO").crear(PASARELA_MP, _intencion(), URLS)
    assert r.token == "PREF-1" and r.metodo == "GET" and "pref_id=PREF-1" in r.url
    ll = doble_mp["llamadas"][0]
    assert ll["headers"]["authorization"] == "Bearer TEST-123"
    assert ll["headers"]["x-idempotency-key"] == "pref-7d1c1e0a-0000-4000-8000-000000000001"
    c = ll["cuerpo"]
    assert c["items"][0]["unit_price"] == 14600 and c["items"][0]["currency_id"] == "CLP"
    assert c["external_reference"] == "PAPRUEBA0000000000000000AB" and c["expires"] is True
    assert c["back_urls"]["success"].endswith("intencion=7d1c1e0a-0000-4000-8000-000000000001")
    assert c["auto_return"] == "approved" and "intencion=" in c["notification_url"]


def test_mp_en_local_sin_notificacion_ni_auto_return(doble_mp):
    doble_mp["respuestas"]["/checkout/preferences"] = (201, {"id": "P", "init_point": "https://x"})
    adaptador_de("MERCADOPAGO").crear(PASARELA_MP, _intencion(), URLS_LOCAL)
    c = doble_mp["llamadas"][0]["cuerpo"]
    assert "notification_url" not in c and "auto_return" not in c


def test_mp_no_confia_en_datos_del_retorno():
    assert adaptador_de("MERCADOPAGO").token_de({"payment_id": "123", "status": "approved", "data.id": "9"}) is None


def _pago(**c):
    return {"id": 555, "status": "approved", "status_detail": "accredited", "transaction_amount": 14600,
            "currency_id": "CLP", "payment_method_id": "visa", "payment_type_id": "credit_card",
            "external_reference": "PAPRUEBA0000000000000000AB", "authorization_code": "AB12",
            "card": {"last_four_digits": "4242", "cardholder": {"name": "NO GUARDAR"}},
            "payer": {"email": "no-guardar@x.cl"}, **c}


def test_mp_consultar_aprobado_sin_datos_sensibles(doble_mp):
    doble_mp["respuestas"]["/v1/payments/search"] = (200, {"results": [_pago()]})
    r = adaptador_de("MERCADOPAGO").consultar(PASARELA_MP, _intencion())
    assert (r.estado, r.monto, r.id_transaccion, r.ultimos_digitos, r.autorizacion) == ("APROBADO", 14600, "555", "4242", "AB12")
    assert "payer" not in r.crudo and "card" not in r.crudo
    assert doble_mp["llamadas"][0]["params"]["external_reference"] == "PAPRUEBA0000000000000000AB"


def test_mp_ignora_pagos_de_otra_orden(doble_mp):
    doble_mp["respuestas"]["/v1/payments/search"] = (200, {"results": [_pago(external_reference="OTRA")]})
    assert adaptador_de("MERCADOPAGO").consultar(PASARELA_MP, _intencion()).estado == "PENDIENTE"


@pytest.mark.parametrize("pagos,estado,motivo", [
    ([], "PENDIENTE", None),
    ([{"status": "in_process"}], "PENDIENTE", None),
    ([{"status": "rejected", "status_detail": "cc_rejected_insufficient_amount"}], "PENDIENTE", "Fondos insuficientes"),
    ([{"status": "approved"}, {"status": "rejected"}], "APROBADO", None),   # reintentó y pagó
    ([{"status": "refunded"}], "RECHAZADO", "Pago devuelto"),
])
def test_mp_mapeo(doble_mp, pagos, estado, motivo):
    doble_mp["respuestas"]["/v1/payments/search"] = (200, {"results": [_pago(**p) for p in pagos]})
    r = adaptador_de("MERCADOPAGO").consultar(PASARELA_MP, _intencion())
    assert r.estado == estado and r.motivo == motivo


def test_mp_probar_y_errores(doble_mp):
    doble_mp["respuestas"]["/users/me"] = (200, {"id": 1})
    adaptador_de("MERCADOPAGO").probar(PASARELA_MP)
    doble_mp["respuestas"]["/users/me"] = (401, {"message": "invalid access token"})
    with pytest.raises(ErrorPasarela) as e:
        adaptador_de("MERCADOPAGO").probar(PASARELA_MP)
    assert e.value.credenciales
    with pytest.raises(ErrorPasarela) as e:
        adaptador_de("MERCADOPAGO").probar(replace(PASARELA_MP, credenciales={}))
    assert e.value.credenciales


# ---------------------------------------------------------------- modo demo (add-delivery-por-comuna)
def _pasarela_bd(proveedor="KHIPU", ambiente="INTEGRACION", activo=True):
    from types import SimpleNamespace
    return SimpleNamespace(proveedor=proveedor, ambiente=ambiente, activo=activo)


def test_modo_demo_en_produccion(monkeypatch):
    from services import pagos_online
    from services.pasarelas import config
    monkeypatch.delenv("ENTORNO", raising=False)
    monkeypatch.setenv("PASARELAS_CLAVE_DEMO", "clave-demo-larga")
    assert config.es_demo("clave-demo-larga") is True
    assert config.es_demo("otra") is False
    assert config.es_demo(None) is False
    integ, prod = _pasarela_bd(), _pasarela_bd(ambiente="PRODUCCION")
    assert pagos_online.puede_cobrar(integ) is False
    assert pagos_online.puede_cobrar(integ, demo=True) is True
    assert pagos_online.puede_cobrar(prod) is True
    assert pagos_online.puede_cobrar(_pasarela_bd("SIMULADA"), demo=True) is False
    assert pagos_online.puede_cobrar(_pasarela_bd(activo=False), demo=True) is False


def test_modo_demo_sin_clave_configurada(monkeypatch):
    from services.pasarelas import config
    monkeypatch.delenv("PASARELAS_CLAVE_DEMO", raising=False)
    assert config.es_demo("cualquiera") is False
    monkeypatch.setenv("PASARELAS_CLAVE_DEMO", "  ")
    assert config.es_demo("") is False
