"""
Router para el flujo de Pre-Venta de Cajas Variables.

Flujo operacional:
1. Mañana: Vendedor crea preventas (cliente + lista de cortes + proveedor + cantidad cajas)
2. ~15:00: Se genera PDF por proveedor para enviar al frigorifico
3. Tarde: Persona en andén escanea qr_original de cada caja → sistema sugiere pedido
4. Post-picking: precio real calculado (peso_real × precio_kg) → listo para facturar
"""
from typing import List, Optional
from datetime import date, datetime
import io

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
import pytz

from database.database import get_db
from database.models import (
    Pedido as PedidoModel,
    ItemPedido as ItemPedidoModel,
    EstadoPedido as EstadoPedidoModel,
    Lote as LoteModel,
    Enrolamiento as EnrolamientoModel,
    Proveedor as ProveedorModel,
    PrecioProveedor as PrecioProveedorModel,
    Producto as ProductoModel,
    Cliente as ClienteModel,
    Local as LocalModel,
    LocalCliente as LocalClienteModel,
    AsignacionPicking as AsignacionPickingModel,
    StockCajasProveedor as StockCajasProveedorModel,
    MovimientoStockCajas as MovimientoStockCajasModel,
    User,
)
from routers.auth import get_current_active_user, get_optional_user
from utils.security import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt as jose_jwt
from services.tenant_service import obtener_siguiente_numero_pedido

router = APIRouter()
router_pdf = APIRouter()  # Router sin auth global para el endpoint PDF

TIMEZONE = pytz.timezone("America/Santiago")
TIPO_PEDIDO_CAJAS = 2  # CAJAS_VARIABLES


# --------------------------------------------------
# Schemas
# --------------------------------------------------

class ItemPreventaCreate(BaseModel):
    producto_id: int
    proveedor_id: int
    cantidad: float = Field(..., gt=0, description="Número de cajas pedidas")
    local_cliente_id: Optional[int] = None
    precio_acordado_kg: Optional[float] = Field(
        default=None,
        gt=0,
        description="Precio por kg acordado con el cliente (debe estar entre precio_minimo_kg y precio_kg)",
    )


class PreventaCreate(BaseModel):
    cliente_id: int
    local_id: int
    notas: Optional[str] = None
    tipo_documento_tributario_id: Optional[int] = Field(default=2, description="1=FAC, 2=BOL")
    medio_pago_id: Optional[int] = None
    items: List[ItemPreventaCreate] = Field(..., min_length=1)


class AsignacionPickingCreate(BaseModel):
    lote_id: int
    item_pedido_id: int


class ItemPreventaOut(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    proveedor_id: Optional[int]
    proveedor_nombre: Optional[str]
    cantidad: float
    precio_unitario_venta: float
    local_cliente_id: Optional[int]
    asignaciones_count: int
    asignaciones: List[dict]

    class Config:
        from_attributes = True


class PreventaOut(BaseModel):
    id: int
    numero_pedido: str
    cliente_id: int
    cliente_nombre: str
    local_id: int
    estado: str
    fecha_pedido: datetime
    notas: Optional[str]
    monto_total: float
    vendedor_id: Optional[int] = None
    vendedor_nombre: Optional[str] = None
    medio_pago_id: Optional[int] = None
    medio_pago_nombre: Optional[str] = None
    items: List[ItemPreventaOut]

    class Config:
        from_attributes = True


class LoteCandidato(BaseModel):
    id: int
    codigo_lote: str
    producto_nombre: str
    proveedor_nombre: str
    peso_actual: float
    fecha_vencimiento: Optional[str] = None
    estado: str  # 'disponible' | 'vendido'


class ScanResultOut(BaseModel):
    qr_original: str
    # Cuando múltiples lotes comparten el mismo QR — el operador elige cuál es
    multiples_lotes: bool = False
    lotes_candidatos: List[LoteCandidato] = []
    # Cuando se resuelve a un único lote (único o elegido)
    lote_id: Optional[int] = None
    codigo_lote: Optional[str] = None
    producto_id: Optional[int] = None
    producto_nombre: Optional[str] = None
    proveedor_id: Optional[int] = None
    proveedor_nombre: Optional[str] = None
    peso_actual: Optional[float] = None
    precio_kg: Optional[float] = None
    sugerencias: List[dict] = []


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _get_estado_preventa(db: Session):
    estado = db.query(EstadoPedidoModel).filter(
        EstadoPedidoModel.codigo == "PREVENTA"
    ).first()
    if not estado:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Estado PREVENTA no configurado en la base de datos"
        )
    return estado


def _build_item_out(item: ItemPedidoModel) -> ItemPreventaOut:
    asignaciones = []
    for a in item.asignaciones_picking:
        asignaciones.append({
            "id": a.id,
            "lote_id": a.lote_id,
            "codigo_lote": a.lote.codigo_lote if a.lote else None,
            "qr_original": a.lote.qr_original if a.lote else None,
            "peso_real": float(a.peso_real),
            "precio_kg": float(a.precio_kg),
            "monto_real": float(a.monto_real),
            "fecha_asignacion": a.fecha_asignacion.isoformat() if a.fecha_asignacion else None,
        })
    return ItemPreventaOut(
        id=item.id,
        producto_id=item.producto_id,
        producto_nombre=item.producto.nombre if item.producto else "?",
        proveedor_id=item.proveedor_id,
        proveedor_nombre=item.proveedor.nombre if item.proveedor else None,
        cantidad=item.cantidad,
        precio_unitario_venta=item.precio_unitario_venta,
        local_cliente_id=item.local_cliente_id,
        asignaciones_count=len(asignaciones),
        asignaciones=asignaciones,
    )


def _build_preventa_out(pedido: PedidoModel) -> PreventaOut:
    return PreventaOut(
        id=pedido.id,
        numero_pedido=pedido.numero_pedido,
        cliente_id=pedido.cliente_id,
        cliente_nombre=pedido.cliente.nombre if pedido.cliente else "?",
        local_id=pedido.local_id,
        estado=pedido.estado_pedido.codigo if pedido.estado_pedido else "?",
        fecha_pedido=pedido.fecha_pedido,
        notas=pedido.notas,
        monto_total=float(pedido.monto_total) if pedido.monto_total else 0.0,
        vendedor_id=pedido.usuario_id,
        vendedor_nombre=pedido.usuario.nombre_completo if pedido.usuario else None,
        medio_pago_id=pedido.medio_pago_id,
        medio_pago_nombre=pedido.medio_pago.nombre if pedido.medio_pago else None,
        items=[_build_item_out(i) for i in pedido.items],
    )


# --------------------------------------------------
# Endpoints CRUD
# --------------------------------------------------

@router.post("/", response_model=PreventaOut, status_code=status.HTTP_201_CREATED)
def crear_preventa(
    data: PreventaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crear un pedido de pre-venta de cajas variables."""
    estado_preventa = _get_estado_preventa(db)

    # Validar cliente
    cliente = db.query(ClienteModel).filter(ClienteModel.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Validar local
    local = db.query(LocalModel).filter(LocalModel.id == data.local_id).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local no encontrado")

    # Obtener número de pedido único
    numero_pedido = obtener_siguiente_numero_pedido(db, current_user.tenant_id)

    # Crear pedido
    pedido = PedidoModel(
        tenant_id=current_user.tenant_id,
        numero_pedido=numero_pedido,
        cliente_id=data.cliente_id,
        local_id=data.local_id,
        tipo_pedido_id=TIPO_PEDIDO_CAJAS,
        tipo_documento_tributario_id=data.tipo_documento_tributario_id or 2,
        medio_pago_id=data.medio_pago_id,
        usuario_id=current_user.id,
        monto_total=0.0,
        estado_id=estado_preventa.id,
        es_pagado=False,
        inventario_descontado=False,
        notas=data.notas,
        canal_venta_id=1,  # POS — preventas siempre se crean desde el punto de venta
    )
    db.add(pedido)
    db.flush()  # Obtener ID

    # Cargar medio de pago para verificar si es al contado
    from database.models import MedioPago as MedioPagoModel, Producto as ProductoModel
    medio_pago_obj = db.query(MedioPagoModel).filter(MedioPagoModel.id == data.medio_pago_id).first() if data.medio_pago_id else None
    es_contado = bool(medio_pago_obj and medio_pago_obj.es_contado)

    # Crear items y reservar lotes FIFO
    for item_data in data.items:
        # Obtener precio_kg del proveedor para este producto
        precio_proveedor = db.query(PrecioProveedorModel).filter(
            PrecioProveedorModel.producto_id == item_data.producto_id,
            PrecioProveedorModel.proveedor_id == item_data.proveedor_id,
            PrecioProveedorModel.activo == True,
        ).first()

        precio_kg = float(precio_proveedor.precio_kg) if precio_proveedor else 0.0
        precio_minimo_kg = float(precio_proveedor.precio_minimo_kg) if (precio_proveedor and precio_proveedor.precio_minimo_kg is not None) else None

        # Validar precio acordado si viene del vendedor
        if item_data.precio_acordado_kg is not None:
            if precio_minimo_kg is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"El producto/proveedor no tiene precio mínimo configurado. El administrador debe definirlo antes de permitir descuentos.",
                )
            if item_data.precio_acordado_kg < precio_minimo_kg:
                raise HTTPException(
                    status_code=400,
                    detail=f"El precio acordado ${item_data.precio_acordado_kg:.2f}/kg es inferior al precio mínimo permitido ${precio_minimo_kg:.2f}/kg.",
                )
            if item_data.precio_acordado_kg > precio_kg:
                raise HTTPException(
                    status_code=400,
                    detail=f"El precio acordado ${item_data.precio_acordado_kg:.2f}/kg no puede superar el precio base ${precio_kg:.2f}/kg.",
                )
            precio_efectivo_kg = item_data.precio_acordado_kg
        else:
            precio_efectivo_kg = precio_kg

        # Aplicar descuento contado al precio efectivo
        if es_contado:
            producto_obj = db.query(ProductoModel).filter(ProductoModel.id == item_data.producto_id).first()
            descuento_pct = float(producto_obj.descuento_contado or 0) if producto_obj else 0.0
            if descuento_pct > 0:
                precio_efectivo_kg = round(precio_efectivo_kg * (1 - descuento_pct / 100))
                print(f"💰 [Preventa] Descuento contado {descuento_pct}% aplicado: {precio_kg} → {precio_efectivo_kg}/kg")

        # --- Reserva FIFO de lotes ---
        lotes_disponibles = (
            db.query(LoteModel)
            .join(EnrolamientoModel, LoteModel.enrolamiento_id == EnrolamientoModel.id)
            .filter(
                LoteModel.producto_id == item_data.producto_id,
                EnrolamientoModel.proveedor_id == item_data.proveedor_id,
                LoteModel.disponible_venta == True,
                LoteModel.vendido == False,
                LoteModel.reservado == False,
            )
            .order_by(LoteModel.fecha_vencimiento.asc())
            .limit(int(item_data.cantidad))
            .all()
        )
        if len(lotes_disponibles) < int(item_data.cantidad):
            producto_nombre = db.query(ProductoModel).filter(ProductoModel.id == item_data.producto_id).first()
            proveedor_nombre = db.query(ProveedorModel).filter(ProveedorModel.id == item_data.proveedor_id).first()
            disponibles_count = (
                db.query(LoteModel)
                .join(EnrolamientoModel, LoteModel.enrolamiento_id == EnrolamientoModel.id)
                .filter(
                    LoteModel.producto_id == item_data.producto_id,
                    EnrolamientoModel.proveedor_id == item_data.proveedor_id,
                    LoteModel.disponible_venta == True,
                    LoteModel.vendido == False,
                    LoteModel.reservado == False,
                )
                .count()
            )
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente de '{producto_nombre.nombre if producto_nombre else item_data.producto_id}' "
                       f"(Proveedor: {proveedor_nombre.nombre if proveedor_nombre else item_data.proveedor_id}). "
                       f"Disponibles: {disponibles_count}, solicitadas: {int(item_data.cantidad)}"
            )

        for lote in lotes_disponibles:
            lote.reservado = True
            # Registrar movimiento de reserva para que la cancelación pueda encontrarlo
            movimiento_reserva = MovimientoStockCajasModel(
                producto_id=item_data.producto_id,
                proveedor_id=item_data.proveedor_id,
                tipo_movimiento="RESERVA_LOTE",
                cajas_movimiento=1,
                peso_total_kg=float(lote.peso_actual),
                descripcion=f"Reserva lote {lote.codigo_lote} para preventa",
                referencia_tipo="PEDIDO",
                referencia_id=pedido.id,
                lote_codigo=lote.codigo_lote,
                usuario=current_user.email,
            )
            db.add(movimiento_reserva)

        # Forzar persistencia en BD para que los próximos ítems del mismo pedido
        # no vean estos lotes como disponibles en su consulta FIFO
        db.flush()

        # Descontar del stock disponible
        stock = db.query(StockCajasProveedorModel).filter(
            StockCajasProveedorModel.producto_id == item_data.producto_id,
            StockCajasProveedorModel.proveedor_id == item_data.proveedor_id,
        ).first()
        if stock and stock.cajas_disponibles >= int(item_data.cantidad):
            stock.cajas_disponibles -= int(item_data.cantidad)
        # --- Fin reserva ---

        item = ItemPedidoModel(
            pedido_id=pedido.id,
            producto_id=item_data.producto_id,
            proveedor_id=item_data.proveedor_id,
            cantidad=item_data.cantidad,
            precio_unitario_venta=precio_efectivo_kg,
            local_cliente_id=item_data.local_cliente_id,
        )
        db.add(item)

    db.commit()

    # Recargar con relaciones
    db.refresh(pedido)
    pedido = (
        db.query(PedidoModel)
        .options(
            joinedload(PedidoModel.cliente),
            joinedload(PedidoModel.estado_pedido),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.producto),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.proveedor),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.asignaciones_picking)
            .joinedload(AsignacionPickingModel.lote),
        )
        .filter(PedidoModel.id == pedido.id)
        .first()
    )
    return _build_preventa_out(pedido)


@router.get("/", response_model=List[PreventaOut])
def listar_preventas(
    fecha: Optional[date] = Query(None, description="Fecha del pedido (YYYY-MM-DD), defecto=hoy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listar preventas de un día (defecto: hoy)."""
    estado_preventa = _get_estado_preventa(db)

    target_date = fecha or date.today()
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=pytz.UTC)

    pedidos = (
        db.query(PedidoModel)
        .options(
            joinedload(PedidoModel.cliente),
            joinedload(PedidoModel.estado_pedido),
            joinedload(PedidoModel.usuario),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.producto),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.proveedor),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.asignaciones_picking)
            .joinedload(AsignacionPickingModel.lote),
        )
        .filter(
            PedidoModel.tenant_id == current_user.tenant_id,
            PedidoModel.estado_id == estado_preventa.id,
            PedidoModel.fecha_pedido >= start,
            PedidoModel.fecha_pedido <= end,
        )
        .order_by(PedidoModel.fecha_pedido.desc())
        .all()
    )

    # Filtrar por vendedor si no es admin
    es_admin = current_user.role and current_user.role.nombre.lower() == "admin"
    if not es_admin:
        pedidos = [p for p in pedidos if p.usuario_id == current_user.id]

    return [_build_preventa_out(p) for p in pedidos]


@router.get("/resumen-cajas")
def resumen_cajas_por_vendedor(
    fecha: Optional[date] = Query(None, description="Fecha (YYYY-MM-DD), defecto=hoy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Resumen de cajas vendidas agrupadas por vendedor para una fecha dada.
    Solo incluye pedidos confirmados (excluye CANCELADO y PREVENTA).
    """
    target_date = fecha or date.today()
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=pytz.UTC)

    # Obtener estados a excluir (solo CANCELADO)
    estados_excluir = db.query(EstadoPedidoModel.id).filter(
        EstadoPedidoModel.codigo.in_(["CANCELADO"])
    ).all()
    ids_excluir = [e[0] for e in estados_excluir]

    pedidos = (
        db.query(PedidoModel)
        .options(
            joinedload(PedidoModel.cliente),
            joinedload(PedidoModel.usuario),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.proveedor),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.producto),
        )
        .filter(
            PedidoModel.tenant_id == current_user.tenant_id,
            PedidoModel.tipo_pedido_id == 2,  # CAJAS_VARIABLES
            ~PedidoModel.estado_id.in_(ids_excluir),
            PedidoModel.fecha_pedido >= start,
            PedidoModel.fecha_pedido <= end,
        )
        .order_by(PedidoModel.usuario_id, PedidoModel.fecha_pedido)
        .all()
    )

    # Agrupar por vendedor y por corte
    vendedores: dict = {}
    cortes: dict = {}

    for pedido in pedidos:
        uid = pedido.usuario_id or 0
        nombre = pedido.usuario.nombre_completo if pedido.usuario else "Sin vendedor"
        if uid not in vendedores:
            vendedores[uid] = {
                "vendedor_id": uid,
                "vendedor_nombre": nombre,
                "cantidad_cajas": 0,
                "cantidad_pedidos": 0,
                "pedidos": [],
            }
        total_cajas_pedido = sum(float(item.cantidad) for item in pedido.items)
        vendedores[uid]["cantidad_cajas"] += total_cajas_pedido
        vendedores[uid]["cantidad_pedidos"] += 1
        vendedores[uid]["pedidos"].append({
            "pedido_id": pedido.id,
            "numero_pedido": pedido.numero_pedido,
            "cliente": pedido.cliente.nombre if pedido.cliente else "N/A",
            "cajas": total_cajas_pedido,
            "monto_total": float(pedido.monto_total),
            "estado": pedido.estado_pedido.codigo if pedido.estado_pedido else "N/A",
        })

        # Agrupar items por corte (producto)
        for item in pedido.items:
            prod_id = item.producto_id
            prod_nombre = item.producto.nombre if item.producto else f"Producto #{prod_id}"
            if prod_id not in cortes:
                cortes[prod_id] = {
                    "producto_id": prod_id,
                    "corte": prod_nombre,
                    "total_cajas": 0,
                }
            cortes[prod_id]["total_cajas"] += float(item.cantidad)

    por_vendedor = list(vendedores.values())
    por_corte = sorted(cortes.values(), key=lambda x: x["corte"])

    return {
        "fecha": str(target_date),
        "total_cajas": sum(v["cantidad_cajas"] for v in por_vendedor),
        "total_pedidos": sum(v["cantidad_pedidos"] for v in por_vendedor),
        "por_vendedor": por_vendedor,
        "por_corte": por_corte,
    }


@router.get("/{pedido_id}", response_model=PreventaOut)
def obtener_preventa(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener detalle de una pre-venta específica."""
    pedido = (
        db.query(PedidoModel)
        .options(
            joinedload(PedidoModel.cliente),
            joinedload(PedidoModel.estado_pedido),
            joinedload(PedidoModel.medio_pago),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.producto),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.proveedor),
            joinedload(PedidoModel.items).joinedload(ItemPedidoModel.asignaciones_picking)
            .joinedload(AsignacionPickingModel.lote),
        )
        .filter(
            PedidoModel.id == pedido_id,
            PedidoModel.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pre-venta no encontrada")
    return _build_preventa_out(pedido)


@router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item_preventa(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Eliminar un item de una pre-venta liberando sus lotes reservados y restaurando el stock."""
    item = (
        db.query(ItemPedidoModel)
        .options(
            joinedload(ItemPedidoModel.asignaciones_picking).joinedload(AsignacionPickingModel.lote),
        )
        .filter(ItemPedidoModel.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    # Validar que el pedido pertenece al tenant y está en PREVENTA
    pedido = (
        db.query(PedidoModel)
        .options(joinedload(PedidoModel.estado_pedido))
        .filter(
            PedidoModel.id == item.pedido_id,
            PedidoModel.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pre-venta no encontrada")
    if pedido.estado_pedido.codigo != "PREVENTA":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden modificar preventas en estado PREVENTA. Estado actual: {pedido.estado_pedido.codigo}"
        )

    cajas_a_liberar = int(item.cantidad)

    # 1) Revertir lotes ya asignados en picking
    for asignacion in item.asignaciones_picking:
        lote = asignacion.lote
        if lote:
            lote.vendido = False
            lote.reservado = False
        db.delete(asignacion)
    db.flush()

    # 2) Liberar lotes aún reservados para este item
    #    Identificamos los lotes exactos vía los movimientos de RESERVA_LOTE
    movimientos_reserva = db.query(MovimientoStockCajasModel).filter(
        MovimientoStockCajasModel.tipo_movimiento == "RESERVA_LOTE",
        MovimientoStockCajasModel.referencia_tipo == "PEDIDO",
        MovimientoStockCajasModel.referencia_id == pedido.id,
        MovimientoStockCajasModel.producto_id == item.producto_id,
        MovimientoStockCajasModel.proveedor_id == item.proveedor_id,
    ).all()

    lote_codigos = {m.lote_codigo for m in movimientos_reserva if m.lote_codigo}
    if lote_codigos:
        lotes_reservados = db.query(LoteModel).filter(
            LoteModel.codigo_lote.in_(lote_codigos),
            LoteModel.reservado == True,
        ).all()
        for lote in lotes_reservados:
            lote.reservado = False

    # 3) Restaurar stock disponible
    if item.proveedor_id:
        stock = db.query(StockCajasProveedorModel).filter(
            StockCajasProveedorModel.producto_id == item.producto_id,
            StockCajasProveedorModel.proveedor_id == item.proveedor_id,
        ).first()
        if stock:
            stock.cajas_disponibles += cajas_a_liberar

    # 4) Eliminar el item
    db.delete(item)
    db.flush()

    # 5) Si era el último item, cancelar la preventa completa
    items_restantes = db.query(ItemPedidoModel).filter(ItemPedidoModel.pedido_id == pedido.id).count()
    if items_restantes == 0:
        estado_cancelado = db.query(EstadoPedidoModel).filter(
            EstadoPedidoModel.codigo == "CANCELADO"
        ).first()
        if estado_cancelado:
            pedido.estado_id = estado_cancelado.id
            pedido.monto_total = 0.0

    db.commit()


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_preventa(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancelar una pre-venta (solo si está en estado PREVENTA)."""
    estado_cancelado = db.query(EstadoPedidoModel).filter(
        EstadoPedidoModel.codigo == "CANCELADO"
    ).first()
    if not estado_cancelado:
        raise HTTPException(status_code=500, detail="Estado CANCELADO no configurado")

    pedido = db.query(PedidoModel).filter(
        PedidoModel.id == pedido_id,
        PedidoModel.tenant_id == current_user.tenant_id,
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pre-venta no encontrada")

    if pedido.estado_pedido.codigo != "PREVENTA":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden cancelar preventas en estado PREVENTA. Estado actual: {pedido.estado_pedido.codigo}"
        )

    pedido.estado_id = estado_cancelado.id
    pedido.monto_total = 0.0

    # Recargar items con asignaciones y lotes
    items = (
        db.query(ItemPedidoModel)
        .options(
            joinedload(ItemPedidoModel.asignaciones_picking).joinedload(AsignacionPickingModel.lote),
        )
        .filter(ItemPedidoModel.pedido_id == pedido.id)
        .all()
    )

    for item in items:
        if item.proveedor_id is None:
            continue

        cajas_a_restaurar = int(item.cantidad)

        # 1) Revertir lotes YA asignados (vendido=True, reservado=False)
        for asignacion in item.asignaciones_picking:
            lote = asignacion.lote
            if lote:
                lote.vendido = False
                lote.reservado = False
            db.delete(asignacion)
            cajas_a_restaurar -= 1  # estas cajas se gestionan aquí

        # 2) Liberar lotes aún reservados (pendientes de picking)
        lotes_reservados = (
            db.query(LoteModel)
            .join(EnrolamientoModel, LoteModel.enrolamiento_id == EnrolamientoModel.id)
            .filter(
                LoteModel.producto_id == item.producto_id,
                EnrolamientoModel.proveedor_id == item.proveedor_id,
                LoteModel.disponible_venta == True,
                LoteModel.vendido == False,
                LoteModel.reservado == True,
            )
            .order_by(LoteModel.fecha_vencimiento.desc())
            .limit(cajas_a_restaurar)
            .all()
        )
        for lote in lotes_reservados:
            lote.reservado = False

        # 3) Restaurar stock disponible por la cantidad total del item
        stock = db.query(StockCajasProveedorModel).filter(
            StockCajasProveedorModel.producto_id == item.producto_id,
            StockCajasProveedorModel.proveedor_id == item.proveedor_id,
        ).first()
        if stock:
            stock.cajas_disponibles += int(item.cantidad)

    db.commit()


# --------------------------------------------------
# Helper auth para PDFs (token por header o query param)
# --------------------------------------------------

def _auth_pdf(request: Request, token: Optional[str], db: Session) -> User:
    raw_token = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        raw_token = auth_header[7:]
    if not raw_token and token:
        raw_token = token
    if not raw_token:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jose_jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        tenant_id_val: int = payload.get("tenant_id")
        if not email:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user_query = db.query(User).filter(User.email == email)
        if tenant_id_val:
            user_query = user_query.filter(User.tenant_id == tenant_id_val)
        u = user_query.first()
        if not u or not u.is_active:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return u
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


# --------------------------------------------------
# PDF para Frigorifico: solo corte + total cajas (sumatoria del día)
# --------------------------------------------------

@router_pdf.get("/pdf/frigorifico")
def generar_pdf_frigorifico(
    request: Request,
    fecha: Optional[date] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """PDF resumido para el frigorifico: corte + total cajas del día por proveedor."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    current_user = _auth_pdf(request, token, db)

    estado_preventa = _get_estado_preventa(db)
    target_date = fecha or date.today()
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=pytz.UTC)

    items = (
        db.query(ItemPedidoModel)
        .join(PedidoModel, ItemPedidoModel.pedido_id == PedidoModel.id)
        .join(ProveedorModel, ItemPedidoModel.proveedor_id == ProveedorModel.id)
        .join(ProductoModel, ItemPedidoModel.producto_id == ProductoModel.id)
        .filter(
            PedidoModel.tenant_id == current_user.tenant_id,
            PedidoModel.estado_id == estado_preventa.id,
            PedidoModel.fecha_pedido >= start,
            PedidoModel.fecha_pedido <= end,
            ItemPedidoModel.proveedor_id.isnot(None),
        )
        .options(
            joinedload(ItemPedidoModel.producto),
            joinedload(ItemPedidoModel.proveedor),
        )
        .all()
    )

    if not items:
        raise HTTPException(status_code=404, detail="No hay preventas para esta fecha")

    # Agrupar por proveedor → por producto → sumar cajas
    por_proveedor: dict = {}
    for item in items:
        prov_id = item.proveedor_id
        prov_nombre = item.proveedor.nombre if item.proveedor else f"Proveedor #{prov_id}"
        prod_nombre = item.producto.nombre if item.producto else f"Producto #{item.producto_id}"
        if prov_id not in por_proveedor:
            por_proveedor[prov_id] = {"nombre": prov_nombre, "cortes": {}}
        por_proveedor[prov_id]["cortes"][prod_nombre] = (
            por_proveedor[prov_id]["cortes"].get(prod_nombre, 0) + item.cantidad
        )

    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=16, spaceAfter=4)
    sub_style = ParagraphStyle("sub", parent=styles["Heading2"], alignment=TA_LEFT, fontSize=13, spaceAfter=2)
    normal = styles["Normal"]

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    fecha_str = target_date.strftime("%d/%m/%Y")

    for prov_id, data in sorted(por_proveedor.items(), key=lambda x: x[1]["nombre"]):
        story.append(Paragraph("PEDIDO AL FRIGORIFICO", title_style))
        story.append(Paragraph(f"Proveedor: {data['nombre']}", sub_style))
        story.append(Paragraph(f"Fecha: {fecha_str}", normal))
        story.append(Spacer(1, 0.5*cm))

        tabla_data = [["Corte / Producto", "Total Cajas"]]
        total = 0
        for prod, cant in sorted(data["cortes"].items()):
            tabla_data.append([prod, str(int(cant))])
            total += int(cant)
        tabla_data.append(["TOTAL", str(total)])

        tabla = Table(tabla_data, colWidths=[13*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5a2d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("FONTSIZE", (0, 1), (-1, -2), 11),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d4edda")),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f0f0f0")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
        ]))
        story.append(tabla)
        story.append(Spacer(1, 1.5*cm))

    doc.build(story)
    buffer.seek(0)
    filename = f"frigorifico_{fecha_str.replace('/', '-')}.pdf"
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------
# PDF por proveedor (detalle con cliente y local de entrega)
# --------------------------------------------------

@router_pdf.get("/pdf/proveedor")
def generar_pdf_proveedor(
    request: Request,
    fecha: Optional[date] = Query(None),
    proveedor_id: Optional[int] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """PDF detallado por proveedor: cliente + local de entrega."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    current_user = _auth_pdf(request, token, db)

    estado_preventa = _get_estado_preventa(db)
    target_date = fecha or date.today()
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
    end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=pytz.UTC)

    # Obtener todos los items de preventas del día
    query = (
        db.query(ItemPedidoModel)
        .join(PedidoModel, ItemPedidoModel.pedido_id == PedidoModel.id)
        .join(ProveedorModel, ItemPedidoModel.proveedor_id == ProveedorModel.id)
        .join(ProductoModel, ItemPedidoModel.producto_id == ProductoModel.id)
        .join(ClienteModel, PedidoModel.cliente_id == ClienteModel.id)
        .filter(
            PedidoModel.tenant_id == current_user.tenant_id,
            PedidoModel.estado_id == estado_preventa.id,
            PedidoModel.fecha_pedido >= start,
            PedidoModel.fecha_pedido <= end,
            ItemPedidoModel.proveedor_id.isnot(None),
        )
    )
    if proveedor_id:
        query = query.filter(ItemPedidoModel.proveedor_id == proveedor_id)

    items = query.options(
        joinedload(ItemPedidoModel.pedido).joinedload(PedidoModel.cliente),
        joinedload(ItemPedidoModel.producto),
        joinedload(ItemPedidoModel.proveedor),
        joinedload(ItemPedidoModel.local_cliente),
    ).all()

    if not items:
        raise HTTPException(status_code=404, detail="No hay preventas para los filtros dados")

    # Agrupar por proveedor
    por_proveedor: dict = {}
    for item in items:
        prov_id = item.proveedor_id
        prov_nombre = item.proveedor.nombre if item.proveedor else f"Proveedor #{prov_id}"
        if prov_id not in por_proveedor:
            por_proveedor[prov_id] = {"nombre": prov_nombre, "items": []}
        por_proveedor[prov_id]["items"].append(item)

    # Generar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=16)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Heading2"], alignment=TA_LEFT, fontSize=13)
    normal = styles["Normal"]

    story = []
    fecha_str = target_date.strftime("%d/%m/%Y")

    for prov_id, data in sorted(por_proveedor.items(), key=lambda x: x[1]["nombre"]):
        story.append(Paragraph(f"PEDIDO AL FRIGORIFICO", title_style))
        story.append(Paragraph(f"Proveedor: {data['nombre']}", subtitle_style))
        story.append(Paragraph(f"Fecha: {fecha_str}", normal))
        story.append(Spacer(1, 0.5 * cm))

        # Agrupar por producto y sumar cajas
        por_producto: dict = {}
        clientes_lista = []
        for item in data["items"]:
            prod_nombre = item.producto.nombre if item.producto else f"Producto #{item.producto_id}"
            if prod_nombre not in por_producto:
                por_producto[prod_nombre] = 0.0
            por_producto[prod_nombre] += item.cantidad

            cliente_nombre = item.pedido.cliente.nombre if item.pedido and item.pedido.cliente else "?"
            pedido_num = item.pedido.numero_pedido if item.pedido else "?"
            local_cli = item.local_cliente
            local_nombre = f"{local_cli.nombre} - {local_cli.direccion}" if local_cli else "—"
            clientes_lista.append({
                "producto": prod_nombre,
                "cantidad": item.cantidad,
                "cliente": cliente_nombre,
                "pedido": pedido_num,
                "local": local_nombre,
            })

        # Tabla resumen por corte
        story.append(Paragraph("RESUMEN POR CORTE:", styles["Heading3"]))
        resumen_data = [["Corte / Producto", "Total Cajas"]]
        for prod, cant in sorted(por_producto.items()):
            resumen_data.append([prod, str(int(cant))])

        resumen_table = Table(resumen_data, colWidths=[12 * cm, 4 * cm])
        resumen_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5a2d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(resumen_table)
        story.append(Spacer(1, 0.4 * cm))

        # Tabla detalle por cliente
        story.append(Paragraph("DETALLE POR PEDIDO:", styles["Heading3"]))
        detalle_data = [["N° Pedido", "Cliente", "Corte", "Cajas", "Local de Entrega"]]
        for row in sorted(clientes_lista, key=lambda x: x["producto"]):
            detalle_data.append([
                row["pedido"],
                row["cliente"],
                row["producto"],
                str(int(row["cantidad"])),
                row["local"],
            ])

        detalle_table = Table(detalle_data, colWidths=[2.5 * cm, 4 * cm, 4.5 * cm, 2 * cm, 5 * cm])
        detalle_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a1a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("WORDWRAP", (4, 1), (4, -1), True),
        ]))
        story.append(detalle_table)
        story.append(Spacer(1, 1 * cm))

    doc.build(story)
    buffer.seek(0)

    filename = f"preventa_{fecha_str.replace('/', '-')}.pdf"
    return Response(
        content=buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------
# Picking
# --------------------------------------------------

@router.post("/picking/scan", response_model=ScanResultOut)
def escanear_caja(
    qr_original: str = Query(..., description="Código QR/barcode de la etiqueta del frigorifico"),
    lote_id: Optional[int] = Query(None, description="ID del lote específico cuando hay múltiples con el mismo QR"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Escanea el barcode de una caja en el andén.
    Si hay múltiples lotes con el mismo QR, retorna la lista para que el operador elija.
    Si lote_id se especifica, resuelve directamente ese lote y retorna las sugerencias.
    """
    lote_options = (
        db.query(LoteModel)
        .options(
            joinedload(LoteModel.enrolamiento).joinedload(EnrolamientoModel.proveedor),
            joinedload(LoteModel.producto),
        )
        .filter(LoteModel.qr_original == qr_original)
        .order_by(LoteModel.id.asc())
        .all()
    )
    if not lote_options:
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna caja con código: {qr_original}")

    # Filtrar los que NO están ya asignados en pedidos ACTIVOS (excluir asignaciones de pedidos cancelados)
    estado_cancelado_scan = db.query(EstadoPedidoModel).filter(
        EstadoPedidoModel.codigo == "CANCELADO"
    ).first()
    asignados_ids = {
        row.lote_id for row in db.query(AsignacionPickingModel.lote_id)
        .join(ItemPedidoModel, AsignacionPickingModel.item_pedido_id == ItemPedidoModel.id)
        .join(PedidoModel, ItemPedidoModel.pedido_id == PedidoModel.id)
        .filter(
            AsignacionPickingModel.lote_id.in_([l.id for l in lote_options]),
            PedidoModel.estado_id != estado_cancelado_scan.id if estado_cancelado_scan else True,
        )
        .all()
    }
    disponibles = [
        l for l in lote_options
        if l.id not in asignados_ids          # sin asignación de picking en pedido activo
        and not l.vendido                      # no vendido
        and l.disponible_venta                 # enrolamiento finalizado
        and l.reservado                        # solo lotes reservados para pre-ventas
    ]

    if not disponibles:
        raise HTTPException(
            status_code=400,
            detail="Esta caja no está reservada para ninguna pre-venta activa, o ya fue asignada."
        )

    # Si se especificó lote_id, resolverlo directamente
    if lote_id is not None:
        lote = next((l for l in disponibles if l.id == lote_id), None)
        if not lote:
            raise HTTPException(status_code=400, detail="El lote seleccionado no está disponible o ya fue asignado")
    elif len(disponibles) > 1:
        # Múltiples disponibles: devolver lista para que el operador elija
        return ScanResultOut(
            qr_original=qr_original,
            multiples_lotes=True,
            lotes_candidatos=[
                LoteCandidato(
                    id=l.id,
                    codigo_lote=l.codigo_lote,
                    producto_nombre=l.producto.nombre if l.producto else "?",
                    proveedor_nombre=l.enrolamiento.proveedor.nombre if l.enrolamiento and l.enrolamiento.proveedor else "?",
                    peso_actual=float(l.peso_actual),
                    fecha_vencimiento=l.fecha_vencimiento.strftime("%d/%m/%Y") if l.fecha_vencimiento else None,
                    estado="disponible" if l.disponible_venta and not l.vendido else "vendido" if l.vendido else "no_disponible",
                )
                for l in disponibles
            ],
        )
    else:
        lote = disponibles[0]

    proveedor = lote.enrolamiento.proveedor if lote.enrolamiento else None
    if not proveedor:
        raise HTTPException(status_code=400, detail="El lote no tiene proveedor asociado")

    # Obtener precio_kg actual del proveedor para este producto
    precio_proveedor = db.query(PrecioProveedorModel).filter(
        PrecioProveedorModel.producto_id == lote.producto_id,
        PrecioProveedorModel.proveedor_id == proveedor.id,
        PrecioProveedorModel.activo == True,
    ).first()
    precio_kg = float(precio_proveedor.precio_kg) if precio_proveedor else 0.0

    # Buscar estado PREVENTA
    estado_preventa = _get_estado_preventa(db)

    # Buscar ItemPedidos candidatos (mismo producto + proveedor, en pedido PREVENTA, incompletos)
    candidatos = (
        db.query(ItemPedidoModel)
        .join(PedidoModel, ItemPedidoModel.pedido_id == PedidoModel.id)
        .filter(
            PedidoModel.tenant_id == current_user.tenant_id,
            PedidoModel.estado_id == estado_preventa.id,
            ItemPedidoModel.producto_id == lote.producto_id,
            ItemPedidoModel.proveedor_id == proveedor.id,
        )
        .options(
            joinedload(ItemPedidoModel.pedido).joinedload(PedidoModel.cliente),
            joinedload(ItemPedidoModel.asignaciones_picking),
        )
        .order_by(PedidoModel.fecha_pedido.asc())
        .all()
    )

    # Filtrar los que todavía necesitan más cajas
    sugerencias = []
    for item in candidatos:
        asignados = len(item.asignaciones_picking)
        requeridos = int(item.cantidad)
        if asignados < requeridos:
            cliente_nombre = item.pedido.cliente.nombre if item.pedido and item.pedido.cliente else "?"
            sugerencias.append({
                "item_pedido_id": item.id,
                "pedido_id": item.pedido_id,
                "numero_pedido": item.pedido.numero_pedido if item.pedido else "?",
                "cliente": cliente_nombre,
                "cajas_pedidas": requeridos,
                "cajas_asignadas": asignados,
                "cajas_faltantes": requeridos - asignados,
                "fecha_pedido": item.pedido.fecha_pedido.isoformat() if item.pedido else None,
            })

    return ScanResultOut(
        lote_id=lote.id,
        codigo_lote=lote.codigo_lote,
        qr_original=lote.qr_original or "",
        producto_id=lote.producto_id,
        producto_nombre=lote.producto.nombre if lote.producto else "?",
        proveedor_id=proveedor.id,
        proveedor_nombre=proveedor.nombre,
        peso_actual=float(lote.peso_actual),
        precio_kg=precio_kg,
        sugerencias=sugerencias,
    )


@router.post("/picking/asignar")
def asignar_caja_a_pedido(
    data: AsignacionPickingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Asigna una caja (lote) a un item de pre-venta.
    Crea el AsignacionPicking y recalcula el monto del pedido.
    Retorna si el pedido está completamente picking.
    """
    # Obtener lote
    lote = db.query(LoteModel).options(
        joinedload(LoteModel.enrolamiento).joinedload(EnrolamientoModel.proveedor),
        joinedload(LoteModel.producto),
    ).filter(LoteModel.id == data.lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    # Verificar que no esté ya asignado
    ya_asignado = db.query(AsignacionPickingModel).filter(
        AsignacionPickingModel.lote_id == data.lote_id
    ).first()
    if ya_asignado:
        raise HTTPException(status_code=400, detail="Esta caja ya fue asignada a otro pedido")

    # Obtener item_pedido
    item = db.query(ItemPedidoModel).options(
        joinedload(ItemPedidoModel.pedido),
        joinedload(ItemPedidoModel.asignaciones_picking),
    ).filter(ItemPedidoModel.id == data.item_pedido_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de pedido no encontrado")

    # Verificar que el pedido esté en PREVENTA
    estado_preventa = _get_estado_preventa(db)
    if item.pedido.estado_id != estado_preventa.id:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden asignar cajas a pedidos en estado PREVENTA"
        )

    # Verificar que el item todavía necesite cajas
    asignados_actuales = len(item.asignaciones_picking)
    if asignados_actuales >= int(item.cantidad):
        raise HTTPException(
            status_code=400,
            detail=f"Este item ya tiene todas sus cajas asignadas ({asignados_actuales}/{int(item.cantidad)})"
        )

    # Obtener precio_kg del proveedor
    proveedor = lote.enrolamiento.proveedor if lote.enrolamiento else None
    precio_proveedor = None
    if proveedor:
        precio_proveedor = db.query(PrecioProveedorModel).filter(
            PrecioProveedorModel.producto_id == lote.producto_id,
            PrecioProveedorModel.proveedor_id == proveedor.id,
            PrecioProveedorModel.activo == True,
        ).first()

    # Usar precio_unitario_venta del item (ya incluye descuento contado aplicado en preventa)
    precio_kg = float(item.precio_unitario_venta)
    peso_real = float(lote.peso_actual)
    monto_neto = round(peso_real * precio_kg, 2)

    # Aplicar IVA si el producto no incluye IVA en su precio (precio_kg es neto sin IVA)
    from database.models import Producto as ProductoModel
    producto_obj = db.query(ProductoModel).filter(ProductoModel.id == lote.producto_id).first()
    precio_incluye_iva = producto_obj.precio_incluye_iva if producto_obj else True
    print(f"🔍 [Picking] Producto {lote.producto_id}: precio_incluye_iva={precio_incluye_iva}")
    if not precio_incluye_iva:
        monto_real = round(monto_neto * 1.19)
        print(f"✅ [Picking] IVA aplicado: neto={monto_neto} → total={monto_real}")
    else:
        monto_real = round(monto_neto)

    # Crear asignación
    asignacion = AsignacionPickingModel(
        lote_id=data.lote_id,
        item_pedido_id=data.item_pedido_id,
        peso_real=peso_real,
        precio_kg=precio_kg,
        monto_real=monto_real,
        usuario_id=current_user.id,
    )
    db.add(asignacion)
    db.flush()

    # Marcar lote como vendido y liberar reserva
    lote.vendido = True
    lote.reservado = False

    # Recalcular monto_total del pedido
    pedido = item.pedido
    todos_los_items = db.query(ItemPedidoModel).options(
        joinedload(ItemPedidoModel.asignaciones_picking)
    ).filter(ItemPedidoModel.pedido_id == pedido.id).all()

    nuevo_total = 0.0
    picking_completo = True
    for it in todos_los_items:
        # Refrescar para incluir la asignación recién creada
        db.refresh(it)
        for a in it.asignaciones_picking:
            nuevo_total += float(a.monto_real)
        if len(it.asignaciones_picking) < int(it.cantidad):
            picking_completo = False

    pedido.monto_total = round(nuevo_total)

    # ✅ AUTO-CONFIRMACIÓN: cuando el picking está completo, confirmar automáticamente
    if picking_completo:
        estado_confirmado = db.query(EstadoPedidoModel).filter(
            EstadoPedidoModel.codigo == 'CONFIRMADO'
        ).first()

        if estado_confirmado and pedido.estado_id != estado_confirmado.id:
            pedido.estado_id = estado_confirmado.id
            pedido.inventario_descontado = True

            # Determinar local de despacho (local_defecto del usuario)
            if not pedido.local_despacho_id and current_user.local_defecto_id:
                pedido.local_despacho_id = current_user.local_defecto_id

            # Registrar movimientos VENTA_LOTE y actualizar cajas_totales_vendidas
            for it in todos_los_items:
                for a in it.asignaciones_picking:
                    lote_a = db.query(LoteModel).filter(LoteModel.id == a.lote_id).first()
                    if not lote_a:
                        continue
                    enrol = lote_a.enrolamiento
                    proveedor_id = enrol.proveedor_id if enrol else None

                    # Movimiento VENTA_LOTE (reemplaza RESERVA_LOTE semánticamente)
                    mov_venta = MovimientoStockCajasModel(
                        producto_id=it.producto_id,
                        proveedor_id=proveedor_id,
                        tipo_movimiento="VENTA_LOTE",
                        cajas_movimiento=1,
                        peso_total_kg=float(a.peso_real),
                        descripcion=f"Venta lote {lote_a.codigo_lote} - picking pedido #{pedido.id}",
                        referencia_tipo="PEDIDO",
                        referencia_id=pedido.id,
                        lote_codigo=lote_a.codigo_lote,
                        usuario=current_user.email,
                    )
                    db.add(mov_venta)

                    # Actualizar cajas_totales_vendidas
                    if proveedor_id:
                        stock = db.query(StockCajasProveedorModel).filter(
                            StockCajasProveedorModel.producto_id == it.producto_id,
                            StockCajasProveedorModel.proveedor_id == proveedor_id,
                        ).first()
                        if stock:
                            stock.cajas_totales_vendidas += 1

            # Registrar venta en caja si hay turno abierto
            if pedido.local_despacho_id:
                from database.models import TurnoCaja, OperacionCaja, TipoOperacionCaja, EstadoTurnoCaja
                turno = db.query(TurnoCaja).filter(
                    TurnoCaja.local_id == pedido.local_despacho_id,
                    TurnoCaja.estado == EstadoTurnoCaja.ABIERTO,
                ).first()
                if turno:
                    op_caja = OperacionCaja(
                        turno_caja_id=turno.id,
                        tipo_operacion=TipoOperacionCaja.VENTA,
                        monto=pedido.monto_total,
                        descripcion=f"Venta preventa - Pedido #{pedido.numero_pedido}",
                        pedido_id=pedido.id,
                        medio_pago_id=pedido.medio_pago_id,
                    )
                    db.add(op_caja)

            print(f"✅ Pedido {pedido.numero_pedido} auto-confirmado tras picking completo. Total: ${pedido.monto_total:,.0f}")

            # Generar comisión si el pedido ya estaba pagado (precio real ya fijado aquí)
            if pedido.es_pagado:
                try:
                    from services.comisiones_service import generar_comision
                    generar_comision(pedido, db)
                except Exception:
                    pass  # No bloquear si falla comisión

    db.commit()

    return {
        "asignacion_id": asignacion.id,
        "lote_id": data.lote_id,
        "item_pedido_id": data.item_pedido_id,
        "peso_real": peso_real,
        "precio_kg": precio_kg,
        "monto_real": monto_real,
        "monto_total_pedido": nuevo_total,
        "picking_completo": picking_completo,
        "mensaje": "Caja asignada correctamente" + (" - ¡Picking completo! Pedido confirmado automáticamente." if picking_completo else ""),
    }


@router.delete("/picking/asignacion/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_caja(
    asignacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Eliminar una asignación de picking (deshacer el escaneo)."""
    asignacion = db.query(AsignacionPickingModel).options(
        joinedload(AsignacionPickingModel.item_pedido).joinedload(ItemPedidoModel.pedido)
    ).filter(AsignacionPickingModel.id == asignacion_id).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    # Verificar tenant
    pedido = asignacion.item_pedido.pedido
    if pedido.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    estado_preventa = _get_estado_preventa(db)
    if pedido.estado_id != estado_preventa.id:
        raise HTTPException(status_code=400, detail="Solo se puede desasignar en pedidos PREVENTA")

    item = asignacion.item_pedido
    lote_desasignado = db.query(LoteModel).filter(LoteModel.id == asignacion.lote_id).first()
    db.delete(asignacion)
    db.flush()

    # Restaurar la reserva del lote: vuelve a estar apartado para esta preventa
    if lote_desasignado:
        lote_desasignado.vendido = False
        lote_desasignado.reservado = True

    # Recalcular monto
    todos_los_items = db.query(ItemPedidoModel).options(
        joinedload(ItemPedidoModel.asignaciones_picking)
    ).filter(ItemPedidoModel.pedido_id == pedido.id).all()

    nuevo_total = sum(
        float(a.monto_real)
        for it in todos_los_items
        for a in it.asignaciones_picking
    )
    pedido.monto_total = nuevo_total
    db.commit()
