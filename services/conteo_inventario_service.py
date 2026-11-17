"""
Servicio de Conteo de Inventario (change OpenSpec: add-conteo-inventario).

Flujo: iniciar (COMPLETO precarga / PARCIAL vacío) -> agregar productos -> registrar
cantidades -> finalizar (ajusta stock por diferencia + movimientos AJUSTE_CONTEO) o cancelar.
Todo filtrado por el tenant del usuario. Funciones síncronas (BD síncrona).
"""
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from utils.alcance_local import exigir_local, local_de_alcance
from database.models import (
    ConteoInventario, ConteoInventarioItem, Inventario, Local, MovimientoInventario, Producto, User,
)

EN_PROCESO = "EN_PROCESO"
FINALIZADO = "FINALIZADO"
CANCELADO = "CANCELADO"
TIPOS = ("COMPLETO", "PARCIAL")
TIPO_MOVIMIENTO = "AJUSTE_CONTEO"
CERO = Decimal("0")
CHILE_TZ = ZoneInfo("America/Santiago")


def _ahora():
    return datetime.now(timezone.utc)


def _nombre_usuario(user: Optional[User]) -> Optional[str]:
    if not user:
        return None
    return user.nombre_completo or user.email


def _dec(valor) -> Decimal:
    return Decimal(str(valor))


# --------------------------------------------------
# Lecturas / validaciones base
# --------------------------------------------------

def _obtener_conteo(db: Session, conteo_id: int, user: User, for_update: bool = False) -> ConteoInventario:
    """Conteo del tenant del usuario (404) y de un local dentro de su alcance (403)."""
    q = db.query(ConteoInventario).filter(
        ConteoInventario.id == conteo_id, ConteoInventario.tenant_id == user.tenant_id
    )
    if for_update:
        q = q.with_for_update()
    conteo = q.first()
    if not conteo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Conteo {conteo_id} no encontrado")
    exigir_local(user, conteo.local_id)  # add-inventario-alcance-por-local
    return conteo


def _exigir_en_proceso(conteo: ConteoInventario):
    if conteo.estado != EN_PROCESO:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"El conteo {conteo.id} está {conteo.estado} y no puede modificarse",
        )


def _stock_actual(db: Session, producto_id: int, local_id: int, for_update: bool = False) -> Optional[Inventario]:
    q = db.query(Inventario).filter(Inventario.producto_id == producto_id, Inventario.local_id == local_id)
    if for_update:
        q = q.with_for_update()
    return q.first()


# --------------------------------------------------
# Iniciar
# --------------------------------------------------

def iniciar_conteo(db: Session, user: User, local_id: int, tipo: str, observacion: Optional[str] = None) -> ConteoInventario:
    tenant_id = user.tenant_id
    if tipo not in TIPOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Tipo inválido: {tipo}")

    local = db.query(Local).filter(Local.id == local_id, Local.tenant_id == tenant_id).first()
    if not local:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Local {local_id} no encontrado")
    exigir_local(user, local_id)  # add-inventario-alcance-por-local

    abierto = db.query(ConteoInventario).filter(
        ConteoInventario.local_id == local_id, ConteoInventario.estado == EN_PROCESO
    ).first()
    if abierto:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"mensaje": f"El local ya tiene un conteo en proceso (#{abierto.id})", "conteo_id": abierto.id},
        )

    conteo = ConteoInventario(
        tenant_id=tenant_id, local_id=local_id, tipo=tipo, estado=EN_PROCESO,
        observacion=observacion, usuario_creador_id=user.id,
    )
    db.add(conteo)
    db.flush()

    if tipo == "COMPLETO":
        producto_ids = [
            pid for (pid,) in db.query(Inventario.producto_id)
            .join(Producto, Producto.id == Inventario.producto_id)
            .filter(Inventario.local_id == local_id, Producto.tenant_id == tenant_id, Producto.activo.is_(True))
            .order_by(Producto.nombre)
            .all()
        ]
        for pid in producto_ids:
            db.add(ConteoInventarioItem(conteo_id=conteo.id, producto_id=pid))

    try:
        db.commit()
    except IntegrityError:
        # Carrera: otro usuario abrió un conteo para el mismo local (índice único parcial)
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="El local ya tiene un conteo en proceso")
    db.refresh(conteo)
    return conteo


# --------------------------------------------------
# Líneas
# --------------------------------------------------

def agregar_items(db: Session, user: User, conteo_id: int, producto_ids: List[int], categoria_id: Optional[int]) -> int:
    """Agrega productos al conteo sin duplicar. Retorna cuántas líneas se crearon."""
    tenant_id = user.tenant_id
    conteo = _obtener_conteo(db, conteo_id, user, for_update=True)
    _exigir_en_proceso(conteo)

    if not producto_ids and categoria_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Indique producto_ids o categoria_id")

    q = db.query(Producto.id).filter(Producto.tenant_id == tenant_id)
    candidatos = set()
    if producto_ids:
        encontrados = {pid for (pid,) in q.filter(Producto.id.in_(producto_ids)).all()}
        faltantes = set(producto_ids) - encontrados
        if faltantes:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Productos no encontrados: {sorted(faltantes)}")
        candidatos |= encontrados
    if categoria_id is not None:
        candidatos |= {
            pid for (pid,) in q.filter(Producto.categoria_id == categoria_id, Producto.activo.is_(True)).all()
        }

    existentes = {
        pid for (pid,) in db.query(ConteoInventarioItem.producto_id)
        .filter(ConteoInventarioItem.conteo_id == conteo.id).all()
    }
    nuevos = candidatos - existentes
    for pid in sorted(nuevos):
        db.add(ConteoInventarioItem(conteo_id=conteo.id, producto_id=pid))
    db.commit()
    return len(nuevos)


def quitar_item(db: Session, user: User, conteo_id: int, item_id: int) -> None:
    conteo = _obtener_conteo(db, conteo_id, user, for_update=True)
    _exigir_en_proceso(conteo)
    if conteo.tipo != "PARCIAL":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Solo se pueden quitar líneas de un conteo PARCIAL")
    item = db.query(ConteoInventarioItem).filter(
        ConteoInventarioItem.id == item_id, ConteoInventarioItem.conteo_id == conteo.id
    ).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Línea {item_id} no encontrada")
    db.delete(item)
    db.commit()


def registrar_cantidad(db: Session, user: User, conteo_id: int, item_id: int, cantidad_contada) -> ConteoInventarioItem:
    if cantidad_contada is None or _dec(cantidad_contada) < CERO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="La cantidad contada debe ser mayor o igual a 0")

    conteo = _obtener_conteo(db, conteo_id, user)
    _exigir_en_proceso(conteo)
    item = db.query(ConteoInventarioItem).filter(
        ConteoInventarioItem.id == item_id, ConteoInventarioItem.conteo_id == conteo.id
    ).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Línea {item_id} no encontrada")

    inv = _stock_actual(db, item.producto_id, conteo.local_id)
    stock_sistema = _dec(inv.cantidad_stock) if inv else CERO
    contado = _dec(cantidad_contada)

    item.stock_sistema = stock_sistema
    item.cantidad_contada = contado
    item.diferencia = contado - stock_sistema
    item.usuario_captura_id = user.id
    item.fecha_captura = _ahora()
    db.commit()
    db.refresh(item)
    return item


# --------------------------------------------------
# Cierre
# --------------------------------------------------

def finalizar_conteo(db: Session, user: User, conteo_id: int) -> ConteoInventario:
    """Aplica en una transacción los ajustes por diferencia y marca el conteo FINALIZADO."""
    tenant_id = user.tenant_id
    usuario_txt = _nombre_usuario(user)
    try:
        conteo = _obtener_conteo(db, conteo_id, user, for_update=True)
        _exigir_en_proceso(conteo)

        items = db.query(ConteoInventarioItem).filter(ConteoInventarioItem.conteo_id == conteo.id).all()
        contados = [i for i in items if i.cantidad_contada is not None]
        if not contados:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="El conteo no tiene ninguna línea contada")

        for item in contados:
            diferencia = _dec(item.diferencia or 0)
            if diferencia == CERO:
                item.ajuste_aplicado = CERO
                continue

            inv = _stock_actual(db, item.producto_id, conteo.local_id, for_update=True)
            if inv is None:
                inv = Inventario(producto_id=item.producto_id, local_id=conteo.local_id, cantidad_stock=CERO)
                db.add(inv)
                db.flush()

            stock_antes = _dec(inv.cantidad_stock)
            stock_despues = stock_antes + diferencia
            nota = f"Conteo #{conteo.id}: contado {item.cantidad_contada} vs sistema {item.stock_sistema}"
            if stock_despues < CERO:
                nota += f" (ajuste truncado: stock no puede quedar negativo; calculado {stock_despues})"
                stock_despues = CERO
            ajuste = stock_despues - stock_antes
            inv.cantidad_stock = stock_despues
            item.ajuste_aplicado = ajuste

            if ajuste != CERO:
                db.add(MovimientoInventario(
                    producto_id=item.producto_id,
                    local_origen_id=conteo.local_id if ajuste < CERO else None,
                    local_destino_id=conteo.local_id if ajuste > CERO else None,
                    cantidad=abs(ajuste),
                    tipo_movimiento=TIPO_MOVIMIENTO,
                    referencia_id=conteo.id,
                    notas=nota,
                    usuario=usuario_txt,
                    usuario_id=user.id,
                ))

        conteo.estado = FINALIZADO
        conteo.usuario_cierre_id = user.id
        conteo.fecha_cierre = _ahora()
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(conteo)
    return conteo


def cancelar_conteo(db: Session, user: User, conteo_id: int) -> ConteoInventario:
    conteo = _obtener_conteo(db, conteo_id, user, for_update=True)
    _exigir_en_proceso(conteo)
    conteo.estado = CANCELADO
    conteo.usuario_cierre_id = user.id
    conteo.fecha_cierre = _ahora()
    db.commit()
    db.refresh(conteo)
    return conteo


# --------------------------------------------------
# Consultas (serialización)
# --------------------------------------------------

def _f(v):
    return float(v) if v is not None else None


def serializar_item(item: ConteoInventarioItem, stock_actual=None) -> dict:
    p = item.producto
    return {
        "id": item.id,
        "producto_id": item.producto_id,
        "sku": p.sku if p else None,
        "producto_nombre": p.nombre if p else None,
        "categoria_id": p.categoria_id if p else None,
        "categoria_nombre": p.categoria.nombre if p and p.categoria else None,
        "unidad": p.unidad_medida.nombre if p and p.unidad_medida else None,
        "stock_sistema": _f(item.stock_sistema),
        "stock_actual": _f(stock_actual),
        "cantidad_contada": _f(item.cantidad_contada),
        "diferencia": _f(item.diferencia),
        "ajuste_aplicado": _f(item.ajuste_aplicado),
        "usuario_captura_id": item.usuario_captura_id,
        "usuario_captura": _nombre_usuario(item.usuario_captura),
        "fecha_captura": item.fecha_captura,
    }


def _resumen(conteo: ConteoInventario, total: int, contados: int, con_dif: int) -> dict:
    return {
        "id": conteo.id,
        "local_id": conteo.local_id,
        "local_nombre": conteo.local.nombre if conteo.local else None,
        "tipo": conteo.tipo,
        "estado": conteo.estado,
        "observacion": conteo.observacion,
        "usuario_creador_id": conteo.usuario_creador_id,
        "usuario_creador": _nombre_usuario(conteo.usuario_creador),
        "fecha_inicio": conteo.fecha_inicio,
        "usuario_cierre_id": conteo.usuario_cierre_id,
        "usuario_cierre": _nombre_usuario(conteo.usuario_cierre),
        "fecha_cierre": conteo.fecha_cierre,
        "total_items": total,
        "items_contados": contados,
        "items_con_diferencia": con_dif,
    }


def listar_conteos(
    db: Session, user: User, local_id: Optional[int] = None, estado: Optional[str] = None,
    desde: Optional[datetime] = None, hasta: Optional[datetime] = None, usuario_id: Optional[int] = None,
    limit: int = 100, offset: int = 0,
) -> List[dict]:
    q = db.query(ConteoInventario).options(
        joinedload(ConteoInventario.local),
        joinedload(ConteoInventario.usuario_creador),
        joinedload(ConteoInventario.usuario_cierre),
    ).filter(ConteoInventario.tenant_id == user.tenant_id)
    propio = local_de_alcance(user)  # usuario de tienda: solo su local
    if propio is not None:
        local_id = propio
    if local_id:
        q = q.filter(ConteoInventario.local_id == local_id)
    if estado:
        q = q.filter(ConteoInventario.estado == estado)
    if desde:
        q = q.filter(ConteoInventario.fecha_inicio >= desde)
    if hasta:
        q = q.filter(ConteoInventario.fecha_inicio <= hasta)
    if usuario_id:
        q = q.filter((ConteoInventario.usuario_creador_id == usuario_id) | (ConteoInventario.usuario_cierre_id == usuario_id))
    conteos = q.order_by(ConteoInventario.fecha_inicio.desc()).offset(offset).limit(limit).all()
    if not conteos:
        return []

    ids = [c.id for c in conteos]
    I = ConteoInventarioItem
    stats = {
        cid: (total, contados or 0, con_dif or 0)
        for cid, total, contados, con_dif in db.query(
            I.conteo_id,
            func.count(I.id),
            func.count(I.cantidad_contada),
            func.sum(case((I.diferencia != 0, 1), else_=0)),
        ).filter(I.conteo_id.in_(ids)).group_by(I.conteo_id).all()
    }
    return [_resumen(c, *stats.get(c.id, (0, 0, 0))) for c in conteos]


def obtener_detalle(db: Session, user: User, conteo_id: int) -> dict:
    conteo = _obtener_conteo(db, conteo_id, user)
    items = db.query(ConteoInventarioItem).options(
        joinedload(ConteoInventarioItem.producto).joinedload(Producto.categoria),
        joinedload(ConteoInventarioItem.producto).joinedload(Producto.unidad_medida),
        joinedload(ConteoInventarioItem.usuario_captura),
    ).filter(ConteoInventarioItem.conteo_id == conteo.id).order_by(ConteoInventarioItem.id).all()

    stocks = {}
    if conteo.estado == EN_PROCESO and items:
        stocks = {
            pid: cant for pid, cant in db.query(Inventario.producto_id, Inventario.cantidad_stock).filter(
                Inventario.local_id == conteo.local_id,
                Inventario.producto_id.in_([i.producto_id for i in items]),
            ).all()
        }

    serial = [serializar_item(i, stocks.get(i.producto_id) if conteo.estado == EN_PROCESO else None) for i in items]
    contados = sum(1 for i in items if i.cantidad_contada is not None)
    con_dif = sum(1 for i in items if i.diferencia is not None and i.diferencia != 0)
    data = _resumen(conteo, len(items), contados, con_dif)
    data["items"] = serial
    return data


# --------------------------------------------------
# Excel
# --------------------------------------------------

def exportar_excel(db: Session, user: User, conteo_id: int) -> tuple[bytes, str]:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    det = obtener_detalle(db, user, conteo_id)
    wb = Workbook()
    ws = wb.active
    ws.title = f"Conteo {det['id']}"

    def fecha(v):
        # Las fechas se guardan en UTC; el Excel se muestra en hora de Chile
        return v.astimezone(CHILE_TZ).strftime("%d-%m-%Y %H:%M") if v else ""

    encabezado = [
        ("Conteo", f"#{det['id']}"),
        ("Local", det["local_nombre"]),
        ("Tipo", det["tipo"]),
        ("Estado", det["estado"]),
        ("Iniciado por", f"{det['usuario_creador'] or ''} — {fecha(det['fecha_inicio'])}"),
        ("Cerrado por", f"{det['usuario_cierre'] or ''} — {fecha(det['fecha_cierre'])}" if det["fecha_cierre"] else ""),
        ("Observación", det["observacion"] or ""),
    ]
    for etiqueta, valor in encabezado:
        ws.append([etiqueta, valor])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    ws.append([])

    columnas = ["SKU", "Producto", "Categoría", "Unidad", "Stock sistema", "Contado",
                "Diferencia", "Ajuste aplicado", "Contado por", "Fecha captura"]
    ws.append(columnas)
    fila_header = ws.max_row
    for c in range(1, len(columnas) + 1):
        cell = ws.cell(row=fila_header, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4F4F4F")

    rojo = PatternFill("solid", fgColor="FDE2E2")
    verde = PatternFill("solid", fgColor="E2F5E2")
    tot_pos = tot_neg = 0.0
    for it in det["items"]:
        ws.append([
            it["sku"], it["producto_nombre"], it["categoria_nombre"], it["unidad"],
            # Línea sin contar en un conteo en proceso: stock actual (sirve como planilla de conteo)
            it["stock_sistema"] if it["stock_sistema"] is not None else it["stock_actual"],
            it["cantidad_contada"] if it["cantidad_contada"] is not None else "No contado",
            it["diferencia"], it["ajuste_aplicado"], it["usuario_captura"] or "", fecha(it["fecha_captura"]),
        ])
        d = it["diferencia"] or 0
        if d < 0:
            tot_neg += d
            ws.cell(row=ws.max_row, column=7).fill = rojo
        elif d > 0:
            tot_pos += d
            ws.cell(row=ws.max_row, column=7).fill = verde

    ws.append([])
    for etiqueta, valor in [
        ("Líneas", det["total_items"]), ("Contadas", det["items_contados"]),
        ("Con diferencia", det["items_con_diferencia"]),
        ("Total sobrantes", round(tot_pos, 3)), ("Total faltantes", round(tot_neg, 3)),
    ]:
        ws.append([etiqueta, valor])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)

    anchos = [14, 40, 20, 12, 14, 12, 12, 15, 28, 18]
    for idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[ws.cell(row=fila_header, column=idx).column_letter].width = ancho
    ws.freeze_panes = ws.cell(row=fila_header + 1, column=1)

    buf = BytesIO()
    wb.save(buf)
    nombre = f"conteo_{det['id']}_{(det['local_nombre'] or 'local').replace(' ', '_')}.xlsx"
    return buf.getvalue(), nombre
