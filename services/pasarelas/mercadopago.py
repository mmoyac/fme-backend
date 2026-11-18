"""Adaptador Mercado Pago — Checkout Pro (change add-pasarelas-pago).

- Autenticación con `Authorization: Bearer <access_token>` (credenciales del vendedor). Las credenciales de prueba
  (de un usuario de prueba vendedor) van en la pasarela de ambiente INTEGRACION; las reales, en PRODUCCION. La URL de la
  API es la misma para ambas.
- `crear` crea una *preferencia* (POST /checkout/preferences) con el monto fijado por el backend y la orden del
  comercio en `external_reference`; el cliente paga en `init_point` (redirección GET).
- El resultado se consulta siempre al servidor de Mercado Pago buscando los pagos por `external_reference`
  (GET /v1/payments/search). Lo que traen el retorno y la notificación (`payment_id`, `status`, `data.id`) se ignora:
  la intención se identifica por el parámetro `intencion` que el backend agrega a sus propias URLs.
- En Checkout Pro el comprador puede reintentar dentro de la misma preferencia tras un rechazo, así que un pago
  rechazado NO es definitivo: se informa como PENDIENTE con su motivo, y la intención vence sola si no llega un aprobado.
"""
from collections.abc import Mapping
from datetime import timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx

from services.pasarelas.base import (APROBADO, PENDIENTE, RECHAZADO, CampoCredencial, ErrorPasarela, Intencion, Pasarela,
                                     Redireccion, Resultado, Urls)

URL_BASE = "https://api.mercadopago.com"
TIMEOUT_S = 10
MARGEN_EXPIRACION = timedelta(minutes=2)    # la preferencia vence un poco después que la intención
# Transporte HTTP reemplazable en los tests (httpx.MockTransport). None = red real.
transporte: httpx.BaseTransport | None = None

EN_CURSO = {"pending", "in_process", "authorized", "in_mediation"}
DEVUELTOS = {"refunded", "charged_back"}
MOTIVOS = {
    "cc_rejected_insufficient_amount": "Fondos insuficientes",
    "cc_rejected_bad_filled_security_code": "Código de seguridad inválido",
    "cc_rejected_bad_filled_date": "Fecha de vencimiento inválida",
    "cc_rejected_bad_filled_card_number": "Número de tarjeta inválido",
    "cc_rejected_bad_filled_other": "Datos de la tarjeta inválidos",
    "cc_rejected_call_for_authorize": "El banco debe autorizar el pago",
    "cc_rejected_card_disabled": "Tarjeta no habilitada",
    "cc_rejected_duplicated_payment": "Pago duplicado",
    "cc_rejected_high_risk": "Pago rechazado por prevención de fraude",
    "cc_rejected_max_attempts": "Se alcanzó el máximo de intentos",
    "cc_rejected_blacklist": "Pago rechazado",
    "cc_rejected_other_reason": "El banco rechazó el pago",
}
_CAMPOS_CRUDO = ("id", "status", "status_detail", "transaction_amount", "currency_id", "payment_method_id",
                 "payment_type_id", "installments", "date_created", "date_approved", "external_reference")


def _entero(v) -> int | None:
    try:
        return int(Decimal(str(v))) if v not in (None, "") else None
    except (InvalidOperation, ValueError):
        return None


def _con_parametros(url: str, **params: str) -> str:
    sep = "&" if "?" in url else "?"
    return url + sep + "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())


def _iso(dt) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")


class MercadoPago:
    codigo = "MERCADOPAGO"
    nombre = "Mercado Pago"
    campos_credenciales = (CampoCredencial("access_token", "Access token", secreto=True),)
    requiere_email = False
    monto_minimo = None
    ruta_comision = None
    # El token guardado es el id de la preferencia, que no sirve para consultar pagos: la verificación se hace siempre
    # por la orden del comercio (external_reference), vía `consultar`.
    verifica_por_intencion = True

    # ---------------------------------------------------------------- HTTP
    def _llamar(self, pasarela: Pasarela, metodo: str, ruta: str, cuerpo: dict | None = None,
                params: dict | None = None, idempotencia: str | None = None) -> dict:
        token = (pasarela.credenciales.get("access_token") or "").strip()
        if not token:
            raise ErrorPasarela("La pasarela Mercado Pago no tiene cargado el access token", credenciales=True)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if idempotencia:
            headers["X-Idempotency-Key"] = idempotencia
        try:
            with httpx.Client(transport=transporte, timeout=TIMEOUT_S) as cliente:
                r = cliente.request(metodo, f"{URL_BASE}{ruta}", json=cuerpo, params=params, headers=headers)
        except httpx.HTTPError as e:
            raise ErrorPasarela("No se pudo contactar a Mercado Pago. Intente nuevamente en unos minutos.",
                                codigo="conexion") from e
        try:
            datos = r.json() if r.content else {}
        except ValueError:
            datos = None
        if 200 <= r.status_code < 300:
            return datos if isinstance(datos, dict) else {}
        mensaje = (datos.get("message") if isinstance(datos, dict) else None) or f"Error {r.status_code} de Mercado Pago"
        if r.status_code in (401, 403):
            raise ErrorPasarela(f"Mercado Pago rechazó el access token: {mensaje}", codigo=str(r.status_code),
                                credenciales=True)
        if r.status_code in (400, 404):
            raise ErrorPasarela(str(mensaje), codigo=str(r.status_code))
        raise ErrorPasarela(f"Respuesta inesperada de Mercado Pago (HTTP {r.status_code})", codigo="conexion")

    # ---------------------------------------------------------------- contrato
    def crear(self, pasarela: Pasarela, intencion: Intencion, urls: Urls) -> Redireccion:
        retorno = _con_parametros(urls.retorno, intencion=intencion.id)
        cuerpo = {
            "items": [{"id": intencion.orden_comercio, "title": intencion.asunto[:250] or "Pedido",
                       "quantity": 1, "currency_id": "CLP", "unit_price": intencion.monto}],
            "external_reference": intencion.orden_comercio,
            "back_urls": {"success": retorno, "failure": retorno, "pending": retorno},
            "expires": True,
            "expiration_date_to": _iso(intencion.expira_en + MARGEN_EXPIRACION),
            "metadata": {"intencion": intencion.id},
        }
        # Mercado Pago solo acepta auto_return y notificaciones hacia URLs públicas (https). Sin notificación, la
        # conciliación registra el pago igual; en desarrollo, URL_PUBLICA_PAGOS (túnel https) la habilita.
        if retorno.startswith("https://"):
            cuerpo["auto_return"] = "approved"
        if urls.notificacion.startswith("https://"):
            cuerpo["notification_url"] = _con_parametros(urls.notificacion, intencion=intencion.id)
        if intencion.email:
            cuerpo["payer"] = {"email": intencion.email}
        d = self._llamar(pasarela, "POST", "/checkout/preferences", cuerpo, idempotencia=f"pref-{intencion.id}")
        url = d.get("init_point") or d.get("sandbox_init_point")
        if not d.get("id") or not url:
            raise ErrorPasarela("Mercado Pago no entregó la URL de pago")
        return Redireccion(url=url, token=str(d["id"]))

    def token_de(self, datos: Mapping[str, str]) -> str | None:
        return None   # se identifica por `intencion` (parámetro propio); nunca por lo que manda Mercado Pago

    def verificar(self, pasarela: Pasarela, token: str) -> Resultado:
        raise ErrorPasarela("Mercado Pago se verifica por la orden del comercio (consultar)")

    def consultar(self, pasarela: Pasarela, intencion: Intencion) -> Resultado:
        d = self._llamar(pasarela, "GET", "/v1/payments/search",
                         params={"external_reference": intencion.orden_comercio, "sort": "date_created",
                                 "criteria": "desc", "limit": 50})
        pagos = [p for p in (d.get("results") or []) if isinstance(p, Mapping)
                 and p.get("external_reference") == intencion.orden_comercio]
        return self._resultado(pagos, intencion.orden_comercio)

    def probar(self, pasarela: Pasarela) -> None:
        self._llamar(pasarela, "GET", "/users/me")

    # ---------------------------------------------------------------- respuesta → Resultado
    @staticmethod
    def _resultado(pagos: list[Mapping], orden: str) -> Resultado:
        aprobados = [p for p in pagos if p.get("status") == "approved"]
        if aprobados:
            p = aprobados[-1]   # el más antiguo aprobado (vienen del más nuevo al más antiguo)
            crudo = {k: p.get(k) for k in _CAMPOS_CRUDO if p.get(k) not in (None, "")}
            if len(aprobados) > 1:
                crudo["otros_aprobados"] = [str(x.get("id")) for x in aprobados[:-1]]
            tarjeta = p.get("card") if isinstance(p.get("card"), Mapping) else {}
            medio = " · ".join(str(x) for x in (p.get("payment_method_id"), p.get("payment_type_id")) if x) or None
            return Resultado(estado=APROBADO, monto=_entero(p.get("transaction_amount")),
                             id_transaccion=str(p["id"]) if p.get("id") is not None else None, orden_comercio=orden,
                             autorizacion=p.get("authorization_code") or None,
                             ultimos_digitos=tarjeta.get("last_four_digits") or None, medio=medio, crudo=crudo)
        if not pagos:
            return Resultado(estado=PENDIENTE, orden_comercio=orden)
        ultimo = pagos[0]
        crudo = {k: ultimo.get(k) for k in _CAMPOS_CRUDO if ultimo.get(k) not in (None, "")}
        if ultimo.get("status") in DEVUELTOS and all(p.get("status") in DEVUELTOS | {"rejected", "cancelled"} for p in pagos):
            return Resultado(estado=RECHAZADO, orden_comercio=orden, motivo="Pago devuelto", crudo=crudo)
        motivo = None
        if ultimo.get("status") in ("rejected", "cancelled"):
            motivo = MOTIVOS.get(ultimo.get("status_detail") or "", "El pago fue rechazado")
        # en curso o rechazado (el comprador puede reintentar en la misma preferencia): no es definitivo
        return Resultado(estado=PENDIENTE, orden_comercio=orden, motivo=motivo, crudo=crudo)
