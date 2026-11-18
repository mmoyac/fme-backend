"""Adaptador Khipu: pago por transferencia bancaria (API de Pagos Instantáneos 3.0; design pasarela-khipu §1).

- Autenticación con la cabecera `x-api-key`, sin firmar las llamadas. La misma URL sirve a la cuenta de cobro de
  desarrollo (bancos de prueba como DemoBank, sin dinero real) y a la real: lo que cambia es la API key.
- El resultado se consulta siempre con `GET /v3/payments/{payment_id}`; la notificación (JSON con `payment_id`) y el
  retorno (que no trae datos de Khipu: lleva el id de la intención en la URL) solo identifican el pago.
- Solo `status = done` con `status_detail = normal` es un pago realizado.
"""
from collections.abc import Mapping
from datetime import timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx

from services.pasarelas.base import (APROBADO, PENDIENTE, RECHAZADO, CampoCredencial, ErrorPasarela, Intencion, Pasarela,
                                Redireccion, Resultado, Urls)

URL_BASE = "https://payment-api.khipu.com/v3"
TIMEOUT_S = 10
MARGEN_EXPIRACION = timedelta(minutes=2)    # el pago en Khipu vence un poco después que la intención
# Transporte HTTP reemplazable en los tests (httpx.MockTransport). None = red real.
transporte: httpx.BaseTransport | None = None

MOTIVOS = {
    "rejected-by-payer": "El pagador rechazó el pago",
    "marked-as-abuse": "El pagador marcó el cobro como no solicitado",
    "reversed": "Pago revertido",
    "partially-refunded": "Pago devuelto parcialmente",
    "fully-refunded": "Pago devuelto",
    "marked-paid-by-receiver": "Marcado como pagado por el cobrador, sin transferencia por Khipu",
}
_CAMPOS_CRUDO = ("payment_id", "transaction_id", "status", "status_detail", "amount", "currency", "bank",
                 "payment_method", "funds_source", "conciliation_date", "authorizer_operation_code",
                 "out_of_date_conciliation", "receipt_url")


def _entero(v) -> int | None:
    try:
        return int(Decimal(str(v))) if v not in (None, "") else None
    except (InvalidOperation, ValueError):
        return None


def _con_parametros(url: str, **params: str) -> str:
    sep = "&" if "?" in url else "?"
    return url + sep + "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())


class Khipu:
    codigo = "KHIPU"
    nombre = "Khipu"
    campos_credenciales = (CampoCredencial("api_key", "API key", secreto=True),)
    requiere_email = False
    monto_minimo = None
    ruta_comision = None   # Khipu no informa la comisión en la consulta del pago

    # ---------------------------------------------------------------- HTTP
    def _llamar(self, pasarela: Pasarela, metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
        api_key = (pasarela.credenciales.get("api_key") or "").strip()
        if not api_key:
            raise ErrorPasarela("La pasarela Khipu no tiene cargada la API key", credenciales=True)
        try:
            with httpx.Client(transport=transporte, timeout=TIMEOUT_S) as cliente:
                r = cliente.request(metodo, f"{URL_BASE}{ruta}", json=cuerpo,
                                    headers={"x-api-key": api_key, "Accept": "application/json"})
        except httpx.HTTPError as e:
            raise ErrorPasarela("No se pudo contactar a Khipu. Intente nuevamente en unos minutos.", codigo="conexion") from e
        try:
            datos = r.json() if r.content else {}
        except ValueError:
            datos = None
        if 200 <= r.status_code < 300:
            return datos if isinstance(datos, dict) else {}
        mensaje = (datos.get("message") if isinstance(datos, dict) else None) or f"Error {r.status_code} de Khipu"
        if r.status_code in (401, 403):
            raise ErrorPasarela(f"Khipu rechazó la API key: {mensaje}", codigo=str(r.status_code), credenciales=True)
        if r.status_code in (400, 404):
            raise ErrorPasarela(str(mensaje), codigo=str(r.status_code))
        raise ErrorPasarela(f"Respuesta inesperada de Khipu (HTTP {r.status_code})", codigo="conexion")

    # ---------------------------------------------------------------- contrato
    def crear(self, pasarela: Pasarela, intencion: Intencion, urls: Urls) -> Redireccion:
        expira = (intencion.expira_en + MARGEN_EXPIRACION).astimezone(timezone.utc)
        cuerpo = {
            "amount": intencion.monto,
            "currency": "CLP",
            "subject": intencion.asunto[:255],
            "transaction_id": intencion.orden_comercio,
            "custom": intencion.id,
            "return_url": _con_parametros(urls.retorno, intencion=intencion.id),
            "cancel_url": _con_parametros(urls.retorno, intencion=intencion.id, cancelado=1),
            "expires_date": expira.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }
        # Khipu notifica desde internet: una URL local (http://…localhost) no le sirve. Sin notificación, la
        # conciliación registra el pago igual; en desarrollo, URL_PUBLICA_PAGOS (túnel https) la habilita.
        if urls.notificacion.startswith("https://"):
            cuerpo.update(notify_url=urls.notificacion, notify_api_version="3.0")
        if intencion.email:
            cuerpo["payer_email"] = intencion.email
        d = self._llamar(pasarela, "POST", "/payments", cuerpo)
        if not d.get("payment_id") or not d.get("payment_url"):
            raise ErrorPasarela("Khipu no entregó la URL de pago")
        return Redireccion(url=d["payment_url"], token=str(d["payment_id"]), id_transaccion=str(d["payment_id"]))

    def token_de(self, datos: Mapping[str, str]) -> str | None:
        t = (datos.get("payment_id") or "").strip()
        return t or None

    def verificar(self, pasarela: Pasarela, token: str) -> Resultado:
        return self._resultado(self._llamar(pasarela, "GET", f"/payments/{quote(token, safe='')}"))

    def consultar(self, pasarela: Pasarela, intencion: Intencion) -> Resultado:
        if not intencion.token:   # Khipu no consulta por la orden del comercio: sin payment_id, la intención vence sola
            raise ErrorPasarela("El pago no alcanzó a crearse en Khipu")
        return self.verificar(pasarela, intencion.token)

    def anular(self, pasarela: Pasarela, token: str) -> None:
        self._llamar(pasarela, "DELETE", f"/payments/{quote(token, safe='')}")

    def probar(self, pasarela: Pasarela) -> None:
        self._llamar(pasarela, "GET", "/banks")

    # ---------------------------------------------------------------- respuesta → Resultado
    @staticmethod
    def _resultado(d: Mapping) -> Resultado:
        estado_k, detalle = (d.get("status") or "").lower(), (d.get("status_detail") or "").lower()
        if estado_k == "done" and detalle == "normal":
            estado = APROBADO
        elif estado_k == "done" and detalle in MOTIVOS:
            estado = RECHAZADO
        else:   # pending, verifying o un valor nuevo: no registra nada, lo resuelve la notificación o la conciliación
            estado = PENDIENTE
        banco = d.get("bank")
        return Resultado(
            estado=estado,
            monto=_entero(d.get("amount")),
            id_transaccion=str(d["payment_id"]) if d.get("payment_id") else None,
            orden_comercio=d.get("transaction_id") or None,
            autorizacion=d.get("authorizer_operation_code") or None,
            medio=f"Transferencia · {banco}" if banco else "Transferencia",
            motivo=MOTIVOS.get(detalle) if estado == RECHAZADO else None,
            crudo={k: d.get(k) for k in _CAMPOS_CRUDO if d.get(k) not in (None, "")},
        )
