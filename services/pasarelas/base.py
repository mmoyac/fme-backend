"""Contrato común de los adaptadores de pasarela (change add-pasarelas-pago; portado de EffiCheck).

El núcleo de pagos (`app/pagos.py`) solo conoce este contrato: crea la transacción, recibe un `Resultado` y lo
confirma de forma idempotente, sin saber de qué proveedor viene. Los códigos de `Resultado.estado` son el vocabulario
del contrato, no un valor persistido: el estado que se guarda es `cat_estado_pago_online`.
"""
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

APROBADO = "APROBADO"
RECHAZADO = "RECHAZADO"
PENDIENTE = "PENDIENTE"


class ErrorPasarela(Exception):
    """Falla al hablar con el proveedor o respuesta inválida. `mensaje` se puede mostrar al usuario."""

    def __init__(self, mensaje: str, *, codigo: str | None = None, credenciales: bool = False):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.credenciales = credenciales   # el proveedor rechazó la apiKey o la firma


@dataclass(frozen=True)
class CampoCredencial:
    codigo: str
    etiqueta: str
    secreto: bool = True


@dataclass(frozen=True)
class Pasarela:
    """Pasarela configurada, con las credenciales ya descifradas (solo viven en memoria durante la llamada)."""
    id: int
    tenant_id: int
    proveedor: str              # cat_proveedor_pasarela.codigo
    ambiente: str               # cat_ambiente_pasarela.codigo: INTEGRACION | PRODUCCION
    nombre_visible: str
    codigo_comercio: str | None = None
    credenciales: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Intencion:
    id: str                     # uuid de ope_pago_online
    orden_comercio: str         # 26 caracteres
    monto: int                  # CLP, entero
    asunto: str
    email: str | None
    expira_en: datetime
    token: str | None = None             # ya creada en el proveedor (para consultar)
    id_transaccion: str | None = None


@dataclass(frozen=True)
class Urls:
    retorno: str                # el navegador vuelve aquí desde el proveedor
    notificacion: str           # el servidor del proveedor avisa aquí (webhook)
    portal: str                 # base del sitio del cliente (landing del tenant), p. ej. https://masasestacion.cl


@dataclass(frozen=True)
class Redireccion:
    url: str
    metodo: str = "GET"                          # GET | POST (formulario oculto)
    campos: Mapping[str, str] = field(default_factory=dict)
    token: str | None = None                     # identificador de la transacción en el proveedor
    id_transaccion: str | None = None


@dataclass(frozen=True)
class Resultado:
    estado: str                                  # APROBADO | RECHAZADO | PENDIENTE
    monto: int | None = None
    id_transaccion: str | None = None
    orden_comercio: str | None = None
    autorizacion: str | None = None
    ultimos_digitos: str | None = None
    medio: str | None = None
    motivo: str | None = None                    # motivo del rechazo, apto para mostrar al cliente
    crudo: Mapping = field(default_factory=dict)  # respuesta filtrada a una lista blanca (sin datos sensibles)


class Adaptador(Protocol):
    codigo: str
    nombre: str
    campos_credenciales: tuple[CampoCredencial, ...]
    requiere_email: bool
    monto_minimo: int | None
    ruta_comision: tuple[str, ...] | None   # ruta de la comisión en respuesta_proveedor; None = no la informa

    def crear(self, pasarela: Pasarela, intencion: Intencion, urls: Urls) -> Redireccion: ...

    def token_de(self, datos: Mapping[str, str]) -> str | None:
        """Identificador de la transacción que traen el retorno o la notificación (nunca prueba de pago)."""

    def verificar(self, pasarela: Pasarela, token: str) -> Resultado:
        """Consulta server-to-server el resultado de la transacción identificada por el token."""

    def consultar(self, pasarela: Pasarela, intencion: Intencion) -> Resultado:
        """Estado actual para la conciliación (por token, id de transacción u orden del comercio)."""

    def probar(self, pasarela: Pasarela) -> None:
        """Lanza ErrorPasarela si las credenciales o la conexión no sirven. No crea transacciones."""

    # Opcional (p. ej. Khipu): `anular(pasarela, token) -> None` elimina en el proveedor una transacción que el cliente
    # canceló, para que ya no pueda pagarse; lanza ErrorPasarela si no es posible (ya iniciada o pagada).
