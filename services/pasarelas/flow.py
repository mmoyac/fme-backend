"""Adaptador Flow (API REST 3.0.1; design pasarelas-pago-flow §2).

- El ambiente de la pasarela decide la URL base: INTEGRACION → sandbox, PRODUCCION → www.flow.cl.
- Firma `s`: HMAC-SHA256 en hexadecimal con la secretKey sobre `nombre+valor` de todos los parámetros (salvo `s`),
  ordenados alfabéticamente por nombre.
- El resultado se consulta siempre al servidor de Flow (getStatusExtended / getStatusByFlowOrderExtended /
  getStatusByCommerceId); el token del retorno o de la notificación solo identifica la transacción.
"""
import hashlib
import hmac
import json
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

from services.pasarelas.base import (APROBADO, PENDIENTE, RECHAZADO, CampoCredencial, ErrorPasarela, Intencion, Pasarela,
                                Redireccion, Resultado, Urls)

URL_BASE = {"INTEGRACION": "https://sandbox.flow.cl/api", "PRODUCCION": "https://www.flow.cl/api"}
TIMEOUT_S = 10
MARGEN_TIMEOUT_S = 120        # la orden de Flow vence un poco después que la intención (el socio pudo partir al final)
ESTADOS = {1: PENDIENTE, 2: APROBADO, 3: RECHAZADO, 4: RECHAZADO}   # 1 pendiente, 2 pagada, 3 rechazada, 4 anulada
# Transporte HTTP reemplazable en los tests (httpx.MockTransport). None = red real.
transporte: httpx.BaseTransport | None = None

_CAMPOS_PAGO = ("date", "media", "mediaType", "amount", "currency", "fee", "balance", "installments", "cardLast4Numbers")
_NO_ENCONTRADA = ("not found", "no existe", "no encontr", "does not exist", "doesn't exist", "not exist")
# Un error que nombra la apiKey o la firma es de credenciales aunque diga "not found" (el sandbox responde
# "501 apiKey not found" a una key de producción). Con credenciales válidas, una orden inexistente da "1700 Transaction not found".
_CREDENCIALES = ("apikey", "api key", "sign", "firma", "secret", "unauthorized", "no autorizado")


def firmar(params: Mapping[str, object], secret_key: str) -> str:
    texto = "".join(f"{k}{params[k]}" for k in sorted(params) if k != "s")
    return hmac.new(secret_key.encode(), texto.encode(), hashlib.sha256).hexdigest()


def _texto(v) -> str:
    if isinstance(v, Decimal):
        return str(int(v)) if v == v.to_integral_value() else str(v)
    return str(v)


def _entero(v) -> int | None:
    try:
        return int(Decimal(str(v))) if v is not None and v != "" else None
    except (InvalidOperation, ValueError):
        return None


class Flow:
    codigo = "FLOW"
    nombre = "Flow"
    campos_credenciales = (CampoCredencial("api_key", "API key", secreto=False),
                           CampoCredencial("secret_key", "Secret key", secreto=True))
    requiere_email = True
    monto_minimo = 350        # CLP (documentación de Flow: "The minimum amount is 350 CLP")
    ruta_comision = ("paymentData", "fee")   # comisión informada por Flow en la respuesta guardada (reporte contable)

    # ---------------------------------------------------------------- HTTP firmado
    def _llamar(self, pasarela: Pasarela, metodo: str, servicio: str, params: Mapping[str, object]) -> dict:
        api_key = (pasarela.credenciales.get("api_key") or "").strip()
        secret = (pasarela.credenciales.get("secret_key") or "").strip()
        if not api_key or not secret:
            raise ErrorPasarela("La pasarela Flow no tiene cargadas la API key y la secret key", credenciales=True)
        base = URL_BASE.get(pasarela.ambiente)
        if not base:
            raise ErrorPasarela(f"Ambiente de pasarela desconocido: {pasarela.ambiente}")
        datos = {k: _texto(v) for k, v in {**params, "apiKey": api_key}.items() if v is not None}
        datos["s"] = firmar(datos, secret)
        try:
            with httpx.Client(transport=transporte, timeout=TIMEOUT_S) as cliente:
                r = (cliente.get(f"{base}/{servicio}", params=datos) if metodo == "GET"
                     else cliente.post(f"{base}/{servicio}", data=datos))
        except httpx.HTTPError as e:
            raise ErrorPasarela("No se pudo contactar a Flow. Intente nuevamente en unos minutos.", codigo="conexion") from e
        try:
            cuerpo = r.json()
        except ValueError:
            cuerpo = None
        if r.status_code == 200 and isinstance(cuerpo, dict):
            return cuerpo
        if r.status_code in (400, 401) and isinstance(cuerpo, dict):
            mensaje = str(cuerpo.get("message") or f"Error {r.status_code} de Flow")
            raise ErrorPasarela(mensaje, codigo=str(cuerpo.get("code", r.status_code)))
        raise ErrorPasarela(f"Respuesta inesperada de Flow (HTTP {r.status_code})", codigo="conexion")

    # ---------------------------------------------------------------- contrato
    def crear(self, pasarela: Pasarela, intencion: Intencion, urls: Urls) -> Redireccion:
        if not intencion.email:
            raise ErrorPasarela("Flow exige el correo del pagador")
        restante = int((intencion.expira_en - datetime.now(timezone.utc)).total_seconds())
        d = self._llamar(pasarela, "POST", "payment/create", {
            "commerceOrder": intencion.orden_comercio,
            "subject": intencion.asunto[:100],
            "currency": "CLP",
            "amount": intencion.monto,
            "email": intencion.email,
            "paymentMethod": 9,
            "urlConfirmation": urls.notificacion,
            "urlReturn": urls.retorno,
            "timeout": max(restante, 60) + MARGEN_TIMEOUT_S,
            "optional": json.dumps({"intencion": intencion.id}, separators=(",", ":")),
        })
        url, token = d.get("url"), d.get("token")
        if not url or not token:
            raise ErrorPasarela("Flow no entregó la URL de pago")
        return Redireccion(url=f"{url}?token={token}", token=str(token),
                           id_transaccion=str(d["flowOrder"]) if d.get("flowOrder") is not None else None)

    def token_de(self, datos: Mapping[str, str]) -> str | None:
        t = (datos.get("token") or "").strip()
        return t or None

    def verificar(self, pasarela: Pasarela, token: str) -> Resultado:
        return self._resultado(self._llamar(pasarela, "GET", "payment/getStatusExtended", {"token": token}))

    def consultar(self, pasarela: Pasarela, intencion: Intencion) -> Resultado:
        if intencion.id_transaccion:
            d = self._llamar(pasarela, "GET", "payment/getStatusByFlowOrderExtended", {"flowOrder": intencion.id_transaccion})
        elif intencion.token:
            d = self._llamar(pasarela, "GET", "payment/getStatusExtended", {"token": intencion.token})
        else:
            d = self._llamar(pasarela, "GET", "payment/getStatusByCommerceId", {"commerceId": intencion.orden_comercio})
        return self._resultado(d)

    def probar(self, pasarela: Pasarela) -> None:
        """Consulta una orden inexistente: con credenciales válidas Flow responde "no encontrada"."""
        try:
            self._llamar(pasarela, "GET", "payment/getStatusByCommerceId", {"commerceId": f"prueba-{uuid.uuid4().hex[:16]}"})
        except ErrorPasarela as e:
            if e.codigo == "conexion" or e.credenciales:
                raise
            texto = e.mensaje.lower()
            if any(x in texto for x in _NO_ENCONTRADA) and not any(x in texto for x in _CREDENCIALES):
                return
            raise ErrorPasarela(f"Flow rechazó las credenciales: {e.mensaje}", codigo=e.codigo, credenciales=True) from e

    # ---------------------------------------------------------------- respuesta → Resultado
    @staticmethod
    def _resultado(d: Mapping) -> Resultado:
        try:
            estado = ESTADOS.get(int(d.get("status")), PENDIENTE)
        except (TypeError, ValueError):
            estado = PENDIENTE      # estado desconocido: no registra nada, lo resuelve la conciliación
        pago = d.get("paymentData") if isinstance(d.get("paymentData"), Mapping) else {}
        error = d.get("lastError") if isinstance(d.get("lastError"), Mapping) else {}
        crudo = {k: d.get(k) for k in ("flowOrder", "commerceOrder", "requestDate", "status", "amount", "currency")
                 if d.get(k) is not None}
        if pago:
            crudo["paymentData"] = {k: pago.get(k) for k in _CAMPOS_PAGO if pago.get(k) is not None}
        if error and (error.get("code") or error.get("message")):
            crudo["lastError"] = {k: error.get(k) for k in ("code", "message") if error.get(k)}
        medio = " · ".join(str(x) for x in (pago.get("media"), pago.get("mediaType")) if x) or None
        return Resultado(
            estado=estado,
            monto=_entero(d.get("amount")),
            id_transaccion=str(d["flowOrder"]) if d.get("flowOrder") is not None else None,
            orden_comercio=d.get("commerceOrder"),
            autorizacion=pago.get("autorizationCode") or None,
            ultimos_digitos=pago.get("cardLast4Numbers") or None,
            medio=medio,
            motivo=(error.get("message") or None) if estado == RECHAZADO else None,
            crudo=crudo,
        )
