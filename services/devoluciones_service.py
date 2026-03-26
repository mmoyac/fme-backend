"""
Servicio para gestión de devoluciones de pedidos entregados.
"""
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database.models import (
    Devolucion, ItemDevolucion, ItemPedido, Inventario,
    MovimientoInventario, Pedido, NotaCredito, TipoDocumento
)
from services.notas_credito_service import MAPA_NOTA_CREDITO


class ItemDevolucionInput:
    def __init__(self, item_pedido_id: int, cantidad_devuelta: float, local_destino_id: int):
        self.item_pedido_id = item_pedido_id
        self.cantidad_devuelta = cantidad_devuelta
        self.local_destino_id = local_destino_id


class DevolucionesService:

    @staticmethod
    def crear(
        pedido: Pedido,
        items_input: List[ItemDevolucionInput],
        motivo: str,
        usuario_id: int,
        db: Session,
    ) -> Devolucion:
        # 1. Validar que el pedido esté entregado
        estado_actual = pedido.estado_pedido.codigo if pedido.estado_pedido else None
        if estado_actual != "ENTREGADO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden hacer devoluciones de pedidos en estado ENTREGADO."
            )

        # 2. Validar que no tenga ya una devolución total
        if pedido.devoluciones:
            monto_ya_devuelto = sum(
                sum(Decimal(str(i.cantidad_devuelta)) * DevolucionesService._precio_unitario(i, db)
                    for i in d.items)
                for d in pedido.devoluciones
            )
            if monto_ya_devuelto >= Decimal(str(pedido.monto_total)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este pedido ya tiene una devolución total registrada."
                )

        # 3. Validar cantidades y calcular monto a devolver
        monto_devolucion = Decimal("0")
        items_validados = []

        for inp in items_input:
            item_pedido = db.query(ItemPedido).filter(
                ItemPedido.id == inp.item_pedido_id,
                ItemPedido.pedido_id == pedido.id,
            ).first()

            if not item_pedido:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {inp.item_pedido_id} no pertenece a este pedido."
                )

            cantidad_devuelta = Decimal(str(inp.cantidad_devuelta))
            if cantidad_devuelta <= 0 or cantidad_devuelta > Decimal(str(item_pedido.cantidad)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cantidad a devolver inválida para {item_pedido.producto.nombre}. "
                           f"Máximo: {item_pedido.cantidad}."
                )

            monto_devolucion += cantidad_devuelta * Decimal(str(item_pedido.precio_unitario_venta))
            items_validados.append((item_pedido, inp, cantidad_devuelta))

        # 4. Crear la devolución
        devolucion = Devolucion(
            tenant_id=pedido.tenant_id,
            pedido_id=pedido.id,
            usuario_id=usuario_id,
            motivo=motivo,
            estado="APROBADA",
        )
        db.add(devolucion)
        db.flush()

        # 5. Crear items y devolver stock
        for item_pedido, inp, cantidad_devuelta in items_validados:
            item_dev = ItemDevolucion(
                devolucion_id=devolucion.id,
                item_pedido_id=item_pedido.id,
                producto_id=item_pedido.producto_id,
                cantidad_devuelta=cantidad_devuelta,
                local_destino_id=inp.local_destino_id,
            )
            db.add(item_dev)

            # Devolver stock al local de destino
            inventario = db.query(Inventario).filter(
                Inventario.producto_id == item_pedido.producto_id,
                Inventario.local_id == inp.local_destino_id,
            ).first()

            if inventario:
                inventario.cantidad_stock += cantidad_devuelta
            else:
                db.add(Inventario(
                    producto_id=item_pedido.producto_id,
                    local_id=inp.local_destino_id,
                    cantidad_stock=cantidad_devuelta,
                ))

            # Registrar movimiento de inventario
            db.add(MovimientoInventario(
                producto_id=item_pedido.producto_id,
                local_destino_id=inp.local_destino_id,
                cantidad=cantidad_devuelta,
                tipo_movimiento="DEVOLUCION",
                referencia_id=pedido.id,
                notas=f"Devolución pedido #{pedido.numero_pedido}",
            ))

        # 6. Crear nota de crédito si corresponde
        nota = DevolucionesService._crear_nota_credito(pedido, monto_devolucion, motivo, db)
        if nota:
            db.flush()
            devolucion.nota_credito_id = nota.id

        return devolucion

    @staticmethod
    def _crear_nota_credito(
        pedido: Pedido, monto: Decimal, motivo: str, db: Session
    ) -> NotaCredito | None:
        if not pedido.tipo_documento_tributario:
            return None

        codigo_nota = MAPA_NOTA_CREDITO.get(pedido.tipo_documento_tributario.codigo)
        if not codigo_nota:
            return None

        tipo_nota = db.query(TipoDocumento).filter(TipoDocumento.codigo == codigo_nota).first()
        if not tipo_nota:
            return None

        nota = NotaCredito(
            tenant_id=pedido.tenant_id,
            pedido_id=pedido.id,
            tipo_documento_id=tipo_nota.id,
            monto=monto,
            motivo=motivo,
            estado_sii="PENDIENTE",
        )
        db.add(nota)

        # Si la factura/boleta no tiene folio SII → anular directamente
        if not pedido.folio_sii:
            pedido.estado_sii = "ANULADO"

        return nota

    @staticmethod
    def _precio_unitario(item_dev: ItemDevolucion, db: Session) -> Decimal:
        item_pedido = db.query(ItemPedido).filter(ItemPedido.id == item_dev.item_pedido_id).first()
        if item_pedido:
            return Decimal(str(item_pedido.precio_unitario_venta))
        return Decimal("0")
