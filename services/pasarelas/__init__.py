"""Pasarelas de pago: registro de adaptadores por código de proveedor (change add-pasarelas-pago; portado de EffiCheck).

Agregar un proveedor (p. ej. Webpay) es escribir su adaptador y registrarlo aquí: la landing, los endpoints de retorno
y notificación y el núcleo de pagos (`services/pagos_online.py`) no cambian.
"""
from services.pasarelas.base import Adaptador
from services.pasarelas.flow import Flow
from services.pasarelas.khipu import Khipu
from services.pasarelas.mercadopago import MercadoPago
from services.pasarelas.simulada import Simulada

_REGISTRO: dict[str, Adaptador] = {a.codigo: a for a in (Simulada(), MercadoPago(), Flow(), Khipu())}

# Medio de pago (tabla medios_pago, maestro global) con el que queda registrado el pedido pagado por cada proveedor.
MEDIO_PAGO_POR_PROVEEDOR = {"MERCADOPAGO": "MERCADOPAGO", "FLOW": "FLOW", "KHIPU": "KHIPU", "SIMULADA": "PAGO_ONLINE"}


def adaptador_de(codigo_proveedor: str) -> Adaptador | None:
    return _REGISTRO.get((codigo_proveedor or "").upper())


def codigos_disponibles() -> list[str]:
    return sorted(_REGISTRO)
