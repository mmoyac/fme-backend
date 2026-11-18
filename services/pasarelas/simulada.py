"""Pasarela simulada: solo desarrollo, nunca con ENTORNO distinto de `desarrollo` ni en ambiente de producción.

No hay proveedor externo: "crear" redirige a la página de la landing que aprueba o rechaza, y esa página envía el
resultado elegido. El resultado se toma tal cual porque no hay a quién consultar; por eso está bloqueada en producción.
"""
from collections.abc import Mapping

from services.pasarelas import config
from services.pasarelas.base import (APROBADO, PENDIENTE, RECHAZADO, ErrorPasarela, Intencion, Pasarela, Redireccion,
                                     Resultado, Urls)


class Simulada:
    codigo = "SIMULADA"
    nombre = "Pasarela simulada (pruebas)"
    campos_credenciales = ()
    requiere_email = False
    monto_minimo = None
    ruta_comision = None

    def _permitida(self, pasarela: Pasarela) -> None:
        if config.es_produccion() or pasarela.ambiente != "INTEGRACION":
            raise ErrorPasarela("La pasarela de prueba no está disponible en producción")

    def crear(self, pasarela: Pasarela, intencion: Intencion, urls: Urls) -> Redireccion:
        self._permitida(pasarela)
        return Redireccion(url=f"{urls.portal}/checkout/simulada?pago={intencion.id}", token=intencion.id)

    def token_de(self, datos: Mapping[str, str]) -> str | None:
        return None

    def verificar(self, pasarela: Pasarela, token: str) -> Resultado:
        raise ErrorPasarela("La pasarela simulada no tiene a quién consultar: se confirma desde su página")

    def resultado_elegido(self, pasarela: Pasarela, intencion: Intencion, aprobado: bool) -> Resultado:
        self._permitida(pasarela)
        return Resultado(estado=APROBADO if aprobado else RECHAZADO, monto=intencion.monto,
                         id_transaccion=f"SIM-{intencion.orden_comercio[:12]}", orden_comercio=intencion.orden_comercio,
                         medio="Simulado", motivo=None if aprobado else "Rechazado en la pasarela de prueba")

    def consultar(self, pasarela: Pasarela, intencion: Intencion) -> Resultado:
        return Resultado(estado=PENDIENTE, orden_comercio=intencion.orden_comercio)   # nunca aprueba sola

    def probar(self, pasarela: Pasarela) -> None:
        self._permitida(pasarela)
