"""
Servicio para gestión de notas de crédito.
"""
from decimal import Decimal
from sqlalchemy.orm import Session

from database.models import NotaCredito, Pedido, TipoDocumento

# Mapeo de tipo de documento del pedido → tipo de nota de crédito correspondiente
# Claves: código del documento original | Valores: código de la nota de crédito
MAPA_NOTA_CREDITO = {
    "BOL": "NOTA_CREDITO_BOLETA",
    "FAC": "NOTA_CREDITO_FACTURA",
}


class NotasCreditoService:

    @staticmethod
    def crear_si_corresponde(pedido: Pedido, db: Session, motivo: str = None) -> NotaCredito | None:
        """
        Crea una nota de crédito por el monto pendiente de acreditar.
        Descuenta lo ya cubierto por notas de crédito anteriores (ej: devoluciones parciales).
        Retorna la nota creada o None si no correspondía crearla o ya estaba cubierto.
        """
        if not pedido.tipo_documento_tributario:
            return None

        codigo_doc = pedido.tipo_documento_tributario.codigo
        codigo_nota = MAPA_NOTA_CREDITO.get(codigo_doc)

        if not codigo_nota:
            return None

        tipo_nota = db.query(TipoDocumento).filter(TipoDocumento.codigo == codigo_nota).first()
        if not tipo_nota:
            return None

        # Calcular monto ya cubierto por NCs anteriores
        ya_acreditado = sum(nc.monto for nc in pedido.notas_credito)
        monto_pendiente = Decimal(str(pedido.monto_total)) - ya_acreditado

        if monto_pendiente <= 0:
            return None  # El pedido ya está 100% acreditado

        nota = NotaCredito(
            tenant_id=pedido.tenant_id,
            pedido_id=pedido.id,
            tipo_documento_id=tipo_nota.id,
            monto=monto_pendiente,
            motivo=motivo,
            estado_sii="PENDIENTE",
        )
        db.add(nota)

        # Si la factura/boleta no tiene folio SII → se anula directamente (solo existe internamente)
        # Si ya tiene folio SII → no tocar, la NC queda PENDIENTE hasta enviarse al SII
        if not pedido.folio_sii:
            pedido.estado_sii = "ANULADO"

        return nota

    @staticmethod
    def obtener_por_pedido(pedido_id: int, db: Session) -> NotaCredito | None:
        return db.query(NotaCredito).filter(NotaCredito.pedido_id == pedido_id).first()
