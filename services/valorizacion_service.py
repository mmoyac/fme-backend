"""Valorización de inventario: stock × costo promedio y stock × precio de venta neto.

Change OpenSpec: add-valorizacion-inventario.
"""
from datetime import date
from io import BytesIO
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import models
from schemas.valorizacion import ValorizacionItem, ValorizacionResponse, ValorizacionTotales

IVA = 1.19

NOTAS_VALORIZACION = [
    "Todos los valores son NETOS (sin IVA), para comparar costo y venta en la misma base.",
    "Costo unitario neto = costo promedio ponderado de compras y producción, por unidad de inventario.",
    "Precio venta neto = precio de lista del local ÷ 1,19 cuando el precio incluye IVA. "
    "La columna 'Precio venta c/IVA' es solo referencia.",
    "Filas 'Sin costo' o 'Sin precio' no suman a la ganancia ni al margen.",
]


def _r(v: Optional[float], nd: int = 2) -> Optional[float]:
    return None if v is None else round(v, nd)


def calcular_valorizacion(
    db: Session,
    tenant_id: int,
    local_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    q: Optional[str] = None,
) -> ValorizacionResponse:
    P, I, L = models.Producto, models.Inventario, models.Local
    C, U, PR = models.CategoriaProducto, models.UnidadMedida, models.Precio

    query = (
        db.query(
            P.id, P.sku, P.nombre, P.categoria_id, C.nombre, L.id, L.nombre, U.simbolo,
            I.cantidad_stock, P.costo_promedio, P.precio_incluye_iva, PR.monto_precio,
        )
        .join(P, P.id == I.producto_id)
        .join(L, L.id == I.local_id)
        .outerjoin(C, C.id == P.categoria_id)
        .outerjoin(U, U.id == P.unidad_medida_id)
        .outerjoin(PR, and_(
            PR.producto_id == P.id,
            PR.local_id == I.local_id,
            PR.unidad_medida_id == P.unidad_medida_id,
        ))
        .filter(P.tenant_id == tenant_id, L.tenant_id == tenant_id, I.cantidad_stock != 0)
    )
    if local_id:
        query = query.filter(I.local_id == local_id)
    if categoria_id:
        query = query.filter(P.categoria_id == categoria_id)
    if q:
        patron = f"%{q.strip()}%"
        query = query.filter(or_(P.nombre.ilike(patron), P.sku.ilike(patron)))

    items = []
    tot = ValorizacionTotales()
    venta_con_costo = 0.0  # valor venta de filas con costo y precio (base del margen global)

    for (pid, sku, nombre, cat_id, cat_nombre, lid, lnombre, unidad,
         stock, costo, incluye_iva, monto) in query.order_by(P.nombre, L.nombre).all():
        stock = float(stock or 0)
        costo = float(costo) if costo is not None else None
        precio_neto = precio_con_iva = None
        if monto is not None:
            precio_neto = float(monto) / IVA if incluye_iva else float(monto)
            precio_con_iva = float(monto) if incluye_iva else float(monto) * IVA

        valor_inv = stock * costo if costo is not None else None
        valor_venta = stock * precio_neto if precio_neto is not None else None
        ganancia = margen = None
        if valor_inv is not None and valor_venta is not None:
            ganancia = valor_venta - valor_inv
            margen = (ganancia / valor_venta * 100) if valor_venta else None

        items.append(ValorizacionItem(
            producto_id=pid, sku=sku, producto_nombre=nombre,
            categoria_id=cat_id, categoria_nombre=cat_nombre,
            local_id=lid, local_nombre=lnombre, unidad=unidad,
            stock=round(stock, 3), costo_unitario=_r(costo, 4),
            valor_inventario=_r(valor_inv), precio_venta_neto=_r(precio_neto),
            precio_venta_con_iva=_r(precio_con_iva), precio_incluye_iva=bool(incluye_iva),
            valor_venta=_r(valor_venta), ganancia_potencial=_r(ganancia), margen_pct=_r(margen),
            sin_costo=costo is None, sin_precio=precio_neto is None, stock_negativo=stock < 0,
        ))

        tot.productos += 1
        if costo is None:
            tot.sin_costo += 1
        else:
            tot.valor_inventario += valor_inv
        if precio_neto is None:
            tot.sin_precio += 1
        else:
            tot.valor_venta += valor_venta
        if ganancia is not None:
            tot.ganancia_potencial += ganancia
            venta_con_costo += valor_venta

    tot.margen_pct = _r(tot.ganancia_potencial / venta_con_costo * 100) if venta_con_costo else None
    tot.valor_inventario = round(tot.valor_inventario, 2)
    tot.valor_venta = round(tot.valor_venta, 2)
    tot.ganancia_potencial = round(tot.ganancia_potencial, 2)
    return ValorizacionResponse(items=items, totales=tot)


def valorizacion_a_excel(data: ValorizacionResponse) -> tuple[bytes, str]:
    """Genera el .xlsx del reporte. Devuelve (contenido, nombre_archivo)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Valorización"
    headers = ["SKU", "Producto", "Categoría", "Local", "Unidad", "Stock", "Costo unitario neto",
               "Valor inventario neto", "Precio venta neto", "Valor venta neto", "Ganancia potencial neta",
               "Margen %", "Precio venta c/IVA (ref.)", "Observación"]
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")

    for it in data.items:
        obs = ", ".join(t for t, f in (("Sin costo", it.sin_costo), ("Sin precio", it.sin_precio),
                                       ("Stock negativo", it.stock_negativo)) if f)
        ws.append([it.sku, it.producto_nombre, it.categoria_nombre, it.local_nombre, it.unidad,
                   it.stock, it.costo_unitario, it.valor_inventario, it.precio_venta_neto,
                   it.valor_venta, it.ganancia_potencial, it.margen_pct, it.precio_venta_con_iva, obs])

    t = data.totales
    ws.append([])
    ws.append(["TOTAL", f"{t.productos} filas", None, None, None, None, None,
               t.valor_inventario, None, t.valor_venta, t.ganancia_potencial, t.margen_pct, None, None])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    fila_totales = ws.max_row

    money = '#,##0'
    for row in ws.iter_rows(min_row=2):
        if row[0].row > fila_totales:
            continue
        for idx in (6, 7, 8, 9, 10, 12):  # G..K y M (0-based)
            row[idx].number_format = money
        row[5].number_format = '#,##0.###'
        row[11].number_format = '0.0'
    ws.append([])
    for nota in NOTAS_VALORIZACION:
        ws.append([nota])
        ws.cell(row=ws.max_row, column=1).font = Font(italic=True, color="555555")
    for col, w in zip("ABCDEFGHIJKLMN", (14, 36, 18, 18, 8, 10, 14, 18, 16, 15, 19, 9, 18, 28)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue(), f"valorizacion_inventario_{date.today().isoformat()}.xlsx"
