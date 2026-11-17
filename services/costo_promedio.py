"""Costo promedio ponderado por producto (change add-valorizacion-inventario).

El costo promedio es neto, por unidad de inventario y global por producto
(suma del stock de todos los locales), igual que en Loyverse.
Debe llamarse ANTES de sumar la cantidad entrante al inventario.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import models


def registrar_entrada_costo(
    db: Session,
    producto_id: int,
    cantidad,
    costo_unitario,
) -> Optional[Decimal]:
    """Recalcula y guarda el costo promedio del producto ante una entrada con costo.

    Devuelve el nuevo costo promedio (o el actual si no se pudo recalcular).
    """
    if cantidad is None or costo_unitario is None:
        return None
    cantidad = Decimal(str(cantidad))
    costo_unitario = Decimal(str(costo_unitario))
    if cantidad <= 0:
        return None

    # Bloquea la fila del producto para que dos entradas simultáneas no se pisen
    producto = (
        db.query(models.Producto)
        .filter(models.Producto.id == producto_id)
        .with_for_update()
        .first()
    )
    if not producto:
        return None

    # SessionLocal tiene autoflush desactivado: flush explícito para que la suma
    # incluya cambios de stock pendientes de esta misma transacción (ej. compra con
    # el mismo producto en dos líneas). Sigue dentro de la transacción, sin commit.
    db.flush()
    stock_total = db.query(func.coalesce(func.sum(models.Inventario.cantidad_stock), 0)).filter(
        models.Inventario.producto_id == producto_id
    ).scalar()
    stock_total = Decimal(str(stock_total or 0))
    costo_actual = producto.costo_promedio

    if stock_total <= 0 or costo_actual is None:
        nuevo = costo_unitario
    else:
        nuevo = (stock_total * Decimal(str(costo_actual)) + cantidad * costo_unitario) / (stock_total + cantidad)

    producto.costo_promedio = nuevo.quantize(Decimal("0.0001"))
    return producto.costo_promedio
