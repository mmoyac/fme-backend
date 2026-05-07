"""
Router para Hojas de Ruta: agrupa pedidos confirmados en salidas de camión,
controla capacidad en kg y permite marcar entregas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text, or_, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.database import get_db
from database.models import (
    HojaRuta, HojaRutaItem, EstadoHojaRuta,
    Pedido, ItemPedido, AsignacionPicking,
    EstadoPedido, Cliente, Vehiculo, User, Producto,
    SolicitudTransferencia, ItemSolicitudTransferencia, EstadoEnrolamiento, Local,
)
from services.webhook_service import trigger_pedido_entregado
from routers.auth import get_current_active_user

router = APIRouter(prefix="/api/hojas-ruta", tags=["Hojas de Ruta"])


# ──────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────

class HojaRutaCreate(BaseModel):
    vehiculo_id: int
    chofer_id: int
    capacidad_kg: Optional[float] = None  # si None, se toma de vehiculo.capacidad_kg
    notas: Optional[str] = None
    pedido_ids: List[int] = []
    solicitud_ids: List[int] = []
    tipo_cobro_chofer: Optional[str] = None   # 'FIJO' o 'POR_KG'
    tarifa_chofer: Optional[float] = None


class HojaRutaUpdate(BaseModel):
    vehiculo_id: Optional[int] = None
    chofer_id: Optional[int] = None
    capacidad_kg: Optional[float] = None
    notas: Optional[str] = None
    estado: Optional[str] = None
    tipo_cobro_chofer: Optional[str] = None
    tarifa_chofer: Optional[float] = None


class PagarChoferRequest(BaseModel):
    monto: Optional[float] = None  # si None, se usa monto_cobro_chofer calculado


class PagarChoferMasivoRequest(BaseModel):
    hoja_ids: List[int]  # rutas a liquidar


class EntregarItemRequest(BaseModel):
    notas_entrega: Optional[str] = None


# ──────────────────────────────────────────
# Helper: kg brutos de un pedido
# ──────────────────────────────────────────

def _kg_pedido(db: Session, items: List) -> float:
    """Calcula el peso total de un pedido.

    Para CAJAS_VARIABLES: usa AsignacionPicking.peso_real (peso físico real de los lotes).
    Para PRODUCTOS regulares: fallback a ItemPedido.cantidad * Producto.peso_bruto.
    """
    if not items:
        return 0.0
    item_ids = [i.id for i in items]
    rows = db.query(
        AsignacionPicking.item_pedido_id,
        func.sum(AsignacionPicking.peso_real).label("total_kg"),
    ).filter(
        AsignacionPicking.item_pedido_id.in_(item_ids)
    ).group_by(AsignacionPicking.item_pedido_id).all()
    peso_por_asignacion = {r.item_pedido_id: float(r.total_kg) for r in rows}

    total = 0.0
    for item in items:
        if item.id in peso_por_asignacion:
            total += peso_por_asignacion[item.id]
        else:
            # Fallback: usar peso_bruto del producto × cantidad
            peso_bruto = float(item.producto.peso_bruto) if item.producto and item.producto.peso_bruto else 0.0
            total += peso_bruto * float(item.cantidad)
    return round(total, 3)


def _build_pedido_summary(pedido: Pedido, db: Session) -> dict:
    kg = _kg_pedido(db, pedido.items or [])
    return {
        "id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "cliente_nombre": pedido.cliente.nombre if pedido.cliente else None,
        "cliente_telefono": pedido.cliente.telefono if pedido.cliente else None,
        "direccion": pedido.cliente.direccion if pedido.cliente else None,
        "monto_total": float(pedido.monto_total) if pedido.monto_total else 0,
        "costo_delivery": float(pedido.costo_delivery) if pedido.costo_delivery else 0,
        "estado": pedido.estado_pedido.codigo if pedido.estado_pedido else None,
        "es_pagado": pedido.es_pagado,
        "kg_brutos": kg,
        "items_count": len(pedido.items) if pedido.items else 0,
    }


def _build_solicitud_summary(s: SolicitudTransferencia) -> dict:
    local_destino = s.local_destino
    local_origen = s.local_origen
    # Calcular kg a partir de cantidad_aprobada × peso_bruto del producto
    kg = 0.0
    for item in (s.items or []):
        cantidad = float(item.cantidad_aprobada or item.cantidad_solicitada or 0)
        peso = float(item.producto.peso_bruto) if item.producto and item.producto.peso_bruto else 0.0
        kg += cantidad * peso
    return {
        "id": s.solicitud_id,
        "tipo": "solicitud",
        "numero_pedido": f"ST-{s.solicitud_id}",
        "cliente_nombre": f"{local_origen.nombre if local_origen else f'Local {s.local_origen_id}'} → {local_destino.nombre if local_destino else f'Local {s.local_destino_id}'}",
        "cliente_telefono": None,
        "direccion": local_destino.direccion if local_destino and hasattr(local_destino, 'direccion') else None,
        "monto_total": 0,
        "costo_delivery": 0,
        "estado": "SOLICITUD",
        "es_pagado": True,
        "kg_brutos": round(kg, 3),
        "items_count": len(s.items) if s.items else 0,
        "fecha_pedido": s.fecha_actualizacion.isoformat() if s.fecha_actualizacion else None,
        "local_origen_nombre": local_origen.nombre if local_origen else f"Local {s.local_origen_id}",
        "local_destino_nombre": local_destino.nombre if local_destino else f"Local {s.local_destino_id}",
    }


def _build_hoja_response(hoja: HojaRuta, db: Session) -> dict:
    items_out = []
    total_kg = 0.0
    for hi in (hoja.items or []):
        if hi.pedido_id and hi.pedido:
            pedido_data = _build_pedido_summary(hi.pedido, db)
            total_kg += pedido_data["kg_brutos"]
            items_out.append({
                "id": hi.id,
                "pedido_id": hi.pedido_id,
                "solicitud_id": None,
                "orden": hi.orden,
                "entregado": hi.entregado,
                "fecha_entrega": hi.fecha_entrega.isoformat() if hi.fecha_entrega else None,
                "notas_entrega": hi.notas_entrega,
                "pedido": pedido_data,
            })
        elif hi.solicitud_id and hi.solicitud:
            sol_data = _build_solicitud_summary(hi.solicitud)
            items_out.append({
                "id": hi.id,
                "pedido_id": None,
                "solicitud_id": hi.solicitud_id,
                "orden": hi.orden,
                "entregado": hi.entregado,
                "fecha_entrega": hi.fecha_entrega.isoformat() if hi.fecha_entrega else None,
                "notas_entrega": hi.notas_entrega,
                "pedido": sol_data,
            })

    # Sort by orden
    items_out.sort(key=lambda x: x["orden"])

    capacidad = float(hoja.capacidad_kg) if hoja.capacidad_kg else None
    # Datos del vehículo
    vehiculo_data = None
    if hoja.vehiculo:
        v = hoja.vehiculo
        vehiculo_data = {
            "id": v.id,
            "patente": v.patente,
            "marca": v.marca,
            "modelo": v.modelo,
            "capacidad_kg": float(v.capacidad_kg) if v.capacidad_kg else None,
            "tipo": v.tipo_vehiculo.nombre if v.tipo_vehiculo else None,
            "label": " — ".join(filter(None, [v.patente, v.marca, v.modelo])),
        }

    # Datos del chofer
    chofer_data = None
    if hoja.chofer:
        chofer_data = {
            "id": hoja.chofer.id,
            "nombre": hoja.chofer.nombre_completo,
            "email": hoja.chofer.email,
        }

    return {
        "id": hoja.id,
        "vehiculo_id": hoja.vehiculo_id,
        "vehiculo": vehiculo_data,
        "chofer_id": hoja.chofer_id,
        "chofer": chofer_data,
        # legacy
        "chofer_nombre": hoja.chofer.nombre_completo if hoja.chofer else hoja.chofer_nombre,
        "patente": hoja.vehiculo.patente if hoja.vehiculo else None,
        "capacidad_kg": capacidad,
        "estado": hoja.estado.value if hoja.estado else None,
        "fecha_creacion": hoja.fecha_creacion.isoformat() if hoja.fecha_creacion else None,
        "fecha_salida": hoja.fecha_salida.isoformat() if hoja.fecha_salida else None,
        "fecha_retorno": hoja.fecha_retorno.isoformat() if hoja.fecha_retorno else None,
        "notas": hoja.notas,
        "total_kg": round(total_kg, 3),
        "capacidad_disponible_kg": round(capacidad - total_kg, 3) if capacidad else None,
        "porcentaje_carga": round((total_kg / capacidad) * 100, 1) if capacidad and capacidad > 0 else None,
        "total_pedidos": len(items_out),
        "pedidos_entregados": sum(1 for i in items_out if i["entregado"]),
        "items": items_out,
        # Cobro chofer
        "tipo_cobro_chofer": hoja.tipo_cobro_chofer,
        "tarifa_chofer": float(hoja.tarifa_chofer) if hoja.tarifa_chofer is not None else None,
        "monto_cobro_chofer": float(hoja.monto_cobro_chofer) if hoja.monto_cobro_chofer is not None else None,
        "cobro_chofer_pagado": hoja.cobro_chofer_pagado,
        "fecha_pago_chofer": hoja.fecha_pago_chofer.isoformat() if hoja.fecha_pago_chofer else None,
    }


def _hoja_options():
    """Opciones de carga para HojaRuta con items de pedido y solicitud."""
    return [
        joinedload(HojaRuta.vehiculo).joinedload(Vehiculo.tipo_vehiculo),
        joinedload(HojaRuta.chofer),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.cliente),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items).joinedload(ItemPedido.producto),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.estado_pedido),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.solicitud).joinedload(SolicitudTransferencia.local_origen),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.solicitud).joinedload(SolicitudTransferencia.local_destino),
        joinedload(HojaRuta.items).joinedload(HojaRutaItem.solicitud).joinedload(SolicitudTransferencia.items).joinedload(ItemSolicitudTransferencia.producto),
    ]


# ──────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────

@router.get("/pedidos-disponibles")
def listar_pedidos_disponibles(
    todos_locales: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Pedidos CONFIRMADOS sin hoja de ruta asignada (para armar nueva ruta)."""
    # IDs ya asignados a alguna hoja de ruta
    asignados = db.query(HojaRutaItem.pedido_id).all()
    asignados_ids = {r[0] for r in asignados}

    estado_confirmado = db.query(EstadoPedido).filter(EstadoPedido.codigo == "CONFIRMADO").first()
    if not estado_confirmado:
        return []

    q_pedidos = (
        db.query(Pedido)
        .join(Cliente)
        .filter(
            Cliente.tenant_id == current_user.tenant_id,
            Pedido.estado_id == estado_confirmado.id,
            ~Pedido.id.in_(asignados_ids) if asignados_ids else True,
        )
    )

    # Filtrar por local del usuario salvo que sea admin o se pidan todos los locales
    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'
    if not todos_locales and not es_admin and current_user.local_defecto_id:
        q_pedidos = q_pedidos.filter(
            or_(
                Pedido.local_despacho_id == current_user.local_defecto_id,
                and_(Pedido.local_despacho_id == None, Pedido.local_id == current_user.local_defecto_id),
            )
        )

    pedidos = (
        q_pedidos
        .options(
            joinedload(Pedido.cliente),
            joinedload(Pedido.items).joinedload(ItemPedido.producto),
            joinedload(Pedido.estado_pedido),
        )
        .order_by(Pedido.fecha_pedido.desc())
        .all()
    )

    result = []
    for p in pedidos:
        kg = _kg_pedido(db, p.items or [])
        result.append({
            "id": p.id,
            "tipo": "pedido",
            "numero_pedido": p.numero_pedido,
            "cliente_nombre": p.cliente.nombre if p.cliente else None,
            "cliente_telefono": p.cliente.telefono if p.cliente else None,
            "direccion": p.cliente.direccion if p.cliente else None,
            "monto_total": float(p.monto_total) if p.monto_total else 0,
            "costo_delivery": float(p.costo_delivery) if p.costo_delivery else 0,
            "es_pagado": p.es_pagado,
            "kg_brutos": round(kg, 3),
            "items_count": len(p.items) if p.items else 0,
            "fecha_pedido": p.fecha_pedido.isoformat() if p.fecha_pedido else None,
        })

    # Solicitudes FINALIZADO con requiere_delivery=True no asignadas a ninguna hoja
    solicitudes_asignadas_ids = {
        r[0] for r in db.query(HojaRutaItem.solicitud_id).filter(HojaRutaItem.solicitud_id.isnot(None)).all()
    }
    estado_finalizado = db.query(EstadoEnrolamiento).filter(EstadoEnrolamiento.codigo == "FINALIZADO").first()
    if estado_finalizado:
        solicitudes = db.query(SolicitudTransferencia).options(
            joinedload(SolicitudTransferencia.local_origen),
            joinedload(SolicitudTransferencia.local_destino),
            joinedload(SolicitudTransferencia.items).joinedload(ItemSolicitudTransferencia.producto),
        ).filter(
            SolicitudTransferencia.tenant_id == current_user.tenant_id,
            SolicitudTransferencia.estado_id == estado_finalizado.id,
            SolicitudTransferencia.requiere_delivery == True,
            SolicitudTransferencia.solicitud_id.notin_(solicitudes_asignadas_ids) if solicitudes_asignadas_ids else True,
        ).all()
        for s in solicitudes:
            result.append(_build_solicitud_summary(s))

    return result


@router.post("/")
def crear_hoja_ruta(
    data: HojaRutaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea una hoja de ruta con los pedidos y/o solicitudes seleccionados."""
    if not data.pedido_ids and not data.solicitud_ids:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un pedido o solicitud")

    # Validar pedidos
    pedidos = []
    if data.pedido_ids:
        estado_confirmado = db.query(EstadoPedido).filter(EstadoPedido.codigo == "CONFIRMADO").first()
        if not estado_confirmado:
            raise HTTPException(status_code=500, detail="Estado CONFIRMADO no encontrado")

        pedidos = (
            db.query(Pedido)
            .join(Cliente)
            .filter(
                Pedido.id.in_(data.pedido_ids),
                Cliente.tenant_id == current_user.tenant_id,
                Pedido.estado_id == estado_confirmado.id,
            )
            .options(joinedload(Pedido.items).joinedload(ItemPedido.producto))
            .all()
        )
        if len(pedidos) != len(data.pedido_ids):
            raise HTTPException(status_code=400, detail="Uno o más pedidos no son válidos o no están confirmados")

        ya_asignados = db.query(HojaRutaItem).filter(
            HojaRutaItem.pedido_id.in_(data.pedido_ids)
        ).first()
        if ya_asignados:
            raise HTTPException(status_code=400, detail="Uno o más pedidos ya están asignados a una hoja de ruta")

    # Validar solicitudes
    solicitudes = []
    if data.solicitud_ids:
        estado_finalizado = db.query(EstadoEnrolamiento).filter(EstadoEnrolamiento.codigo == "FINALIZADO").first()
        if not estado_finalizado:
            raise HTTPException(status_code=500, detail="Estado FINALIZADO no encontrado")

        solicitudes = db.query(SolicitudTransferencia).options(
            joinedload(SolicitudTransferencia.local_origen),
            joinedload(SolicitudTransferencia.local_destino),
            joinedload(SolicitudTransferencia.items).joinedload(ItemSolicitudTransferencia.producto),
        ).filter(
            SolicitudTransferencia.solicitud_id.in_(data.solicitud_ids),
            SolicitudTransferencia.tenant_id == current_user.tenant_id,
            SolicitudTransferencia.estado_id == estado_finalizado.id,
            SolicitudTransferencia.requiere_delivery == True,
        ).all()
        if len(solicitudes) != len(data.solicitud_ids):
            raise HTTPException(status_code=400, detail="Una o más solicitudes no son válidas, no están finalizadas o no requieren delivery")

        ya_asignadas = db.query(HojaRutaItem).filter(
            HojaRutaItem.solicitud_id.in_(data.solicitud_ids)
        ).first()
        if ya_asignadas:
            raise HTTPException(status_code=400, detail="Una o más solicitudes ya están asignadas a una hoja de ruta")

    # Calcular kg totales (solo pedidos contribuyen kg)
    total_kg = sum(_kg_pedido(db, p.items or []) for p in pedidos)

    # Validar vehículo y chofer
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id == data.vehiculo_id,
        Vehiculo.tenant_id == current_user.tenant_id,
        Vehiculo.activo == True,
    ).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o inactivo")

    chofer = db.query(User).filter(
        User.id == data.chofer_id,
        User.tenant_id == current_user.tenant_id,
        User.is_active == True,
    ).first()
    if not chofer:
        raise HTTPException(status_code=404, detail="Chofer (usuario) no encontrado o inactivo")

    # Capacidad: usar la del vehículo si no se especifica
    capacidad_efectiva = data.capacidad_kg if data.capacidad_kg is not None else (
        float(vehiculo.capacidad_kg) if vehiculo.capacidad_kg else None
    )

    if capacidad_efectiva and total_kg > capacidad_efectiva:
        raise HTTPException(
            status_code=400,
            detail=f"Peso total ({total_kg:.1f} kg) supera la capacidad del vehículo ({capacidad_efectiva:.1f} kg)",
        )

    # Calcular monto chofer si es FIJO (para POR_KG se calcula al finalizar)
    monto_cobro_inicial = None
    if data.tipo_cobro_chofer == "FIJO" and data.tarifa_chofer is not None:
        monto_cobro_inicial = data.tarifa_chofer

    # Crear hoja de ruta
    hoja = HojaRuta(
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
        vehiculo_id=data.vehiculo_id,
        chofer_id=data.chofer_id,
        capacidad_kg=capacidad_efectiva,
        notas=data.notas,
        estado=EstadoHojaRuta.PENDIENTE,
        tipo_cobro_chofer=data.tipo_cobro_chofer,
        tarifa_chofer=data.tarifa_chofer,
        monto_cobro_chofer=monto_cobro_inicial,
        cobro_chofer_pagado=False,
    )
    db.add(hoja)
    db.flush()

    estado_en_prep = db.query(EstadoPedido).filter(EstadoPedido.codigo == "EN_PREPARACION").first()
    orden = 0
    for pedido_id in data.pedido_ids:
        db.add(HojaRutaItem(hoja_ruta_id=hoja.id, pedido_id=pedido_id, orden=orden))
        if estado_en_prep:
            pedido_obj = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido_obj:
                pedido_obj.estado_id = estado_en_prep.id
        orden += 1

    for sol_id in data.solicitud_ids:
        db.add(HojaRutaItem(hoja_ruta_id=hoja.id, solicitud_id=sol_id, pedido_id=None, orden=orden))
        orden += 1

    db.commit()
    db.refresh(hoja)

    # Recargar con relaciones
    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja.id)
        .options(*_hoja_options())
        .first()
    )
    return _build_hoja_response(hoja, db)


@router.get("/")
def listar_hojas_ruta(
    estado: Optional[str] = None,
    todos_locales: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista todas las hojas de ruta del tenant, filtradas por local del usuario."""
    q = db.query(HojaRuta).filter(HojaRuta.tenant_id == current_user.tenant_id)
    if estado:
        q = q.filter(HojaRuta.estado == EstadoHojaRuta(estado))

    # Filtrar por local del usuario salvo que sea admin o se pidan todos los locales
    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'
    if not todos_locales and not es_admin and current_user.local_defecto_id:
        hoja_ids_local = (
            db.query(HojaRutaItem.hoja_ruta_id)
            .join(Pedido, HojaRutaItem.pedido_id == Pedido.id)
            .filter(
                or_(
                    Pedido.local_despacho_id == current_user.local_defecto_id,
                    and_(Pedido.local_despacho_id == None, Pedido.local_id == current_user.local_defecto_id),
                )
            )
            .distinct()
            .subquery()
        )
        q = q.filter(HojaRuta.id.in_(hoja_ids_local))

    hojas = (
        q.options(*_hoja_options())
        .order_by(HojaRuta.fecha_creacion.desc())
        .all()
    )
    return [_build_hoja_response(h, db) for h in hojas]


@router.get("/mis-hojas")
def mis_hojas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Devuelve las hojas de ruta asignadas al usuario autenticado como chofer.
    Muestra PENDIENTE, EN_RUTA y COMPLETADA no pagadas.
    Desaparece solo cuando cobro_chofer_pagado = True.
    Agrega resumen de delivery cobrable (pedidos no pagados).
    """
    hojas = (
        db.query(HojaRuta)
        .filter(
            HojaRuta.tenant_id == current_user.tenant_id,
            HojaRuta.chofer_id == current_user.id,
            HojaRuta.cobro_chofer_pagado == False,
        )
        .options(*_hoja_options())
        .order_by(HojaRuta.fecha_creacion.desc())
        .all()
    )

    result = []
    for h in hojas:
        hoja_data = _build_hoja_response(h, db)
        # Cobros de delivery: pedidos no prepagados (cobro en mano, entregados o no)
        cobros = [
            float(hi.pedido.costo_delivery or 0)
            for hi in h.items
            if hi.pedido and not hi.pedido.es_pagado and (hi.pedido.costo_delivery or 0) > 0
        ]
        hoja_data["delivery_cobrable"] = round(sum(cobros), 0)
        hoja_data["delivery_cobros_detalle"] = cobros  # lista individual para desglose
        hoja_data["delivery_total"] = round(sum(
            float(hi.pedido.costo_delivery or 0)
            for hi in h.items
            if hi.pedido
        ), 0)
        result.append(hoja_data)

    return result


@router.get("/{hoja_id}")
def obtener_hoja_ruta(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id)
        .options(*_hoja_options())
        .first()
    )
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")
    return _build_hoja_response(hoja, db)


@router.put("/{hoja_id}")
def actualizar_hoja_ruta(
    hoja_id: int,
    data: HojaRutaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    hoja = db.query(HojaRuta).filter(
        HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id
    ).first()
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")

    if data.vehiculo_id is not None:
        vehiculo = db.query(Vehiculo).filter(
            Vehiculo.id == data.vehiculo_id,
            Vehiculo.tenant_id == current_user.tenant_id,
        ).first()
        if not vehiculo:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        hoja.vehiculo_id = data.vehiculo_id
    if data.chofer_id is not None:
        chofer = db.query(User).filter(
            User.id == data.chofer_id,
            User.tenant_id == current_user.tenant_id,
        ).first()
        if not chofer:
            raise HTTPException(status_code=404, detail="Chofer no encontrado")
        hoja.chofer_id = data.chofer_id
    if data.capacidad_kg is not None:
        hoja.capacidad_kg = data.capacidad_kg
    if data.notas is not None:
        hoja.notas = data.notas
    if data.tipo_cobro_chofer is not None:
        hoja.tipo_cobro_chofer = data.tipo_cobro_chofer
    if data.tarifa_chofer is not None:
        hoja.tarifa_chofer = data.tarifa_chofer
        # Recalcular monto si es FIJO
        if hoja.tipo_cobro_chofer == "FIJO":
            hoja.monto_cobro_chofer = data.tarifa_chofer
    if data.estado is not None:
        nuevo_estado = EstadoHojaRuta(data.estado)
        hoja.estado = nuevo_estado
        if nuevo_estado == EstadoHojaRuta.EN_RUTA and not hoja.fecha_salida:
            hoja.fecha_salida = datetime.now()
        elif nuevo_estado == EstadoHojaRuta.COMPLETADA and not hoja.fecha_retorno:
            hoja.fecha_retorno = datetime.now()

    db.commit()
    db.refresh(hoja)

    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja_id)
        .options(*_hoja_options())
        .first()
    )
    return _build_hoja_response(hoja, db)


@router.post("/{hoja_id}/salir")
def marcar_en_ruta(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Marca la hoja de ruta como EN_RUTA y registra la hora de salida."""
    hoja = db.query(HojaRuta).filter(
        HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id
    ).first()
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")
    if hoja.estado != EstadoHojaRuta.PENDIENTE:
        raise HTTPException(status_code=400, detail="La hoja de ruta ya salió o está completada")

    hoja.estado = EstadoHojaRuta.EN_RUTA
    hoja.fecha_salida = datetime.now()

    # Avanzar todos los pedidos de la ruta a EN_RUTA
    estado_en_ruta = db.query(EstadoPedido).filter(EstadoPedido.codigo == "EN_RUTA").first()
    if estado_en_ruta:
        for hi in hoja.items:
            if hi.pedido and not hi.entregado:
                hi.pedido.estado_id = estado_en_ruta.id

    db.commit()
    return {"ok": True, "estado": "EN_RUTA", "fecha_salida": hoja.fecha_salida.isoformat()}


@router.post("/{hoja_id}/items/{item_id}/entregar")
def marcar_entregado(
    hoja_id: int,
    item_id: int,
    body: EntregarItemRequest = EntregarItemRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Marca un pedido como entregado dentro de la hoja de ruta y
    cambia el estado del pedido a ENTREGADO en el sistema.
    """
    hi = db.query(HojaRutaItem).filter(
        HojaRutaItem.id == item_id,
        HojaRutaItem.hoja_ruta_id == hoja_id,
    ).first()
    if not hi:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    # Verificar que la hoja es del tenant
    hoja = db.query(HojaRuta).filter(
        HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id
    ).first()
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")

    if hi.entregado:
        raise HTTPException(status_code=400, detail="Este pedido ya fue marcado como entregado")

    # Marcar item de hoja de ruta
    hi.entregado = True
    hi.fecha_entrega = datetime.now()
    hi.notas_entrega = body.notas_entrega

    # Cambiar estado del pedido a ENTREGADO
    estado_entregado = db.query(EstadoPedido).filter(EstadoPedido.codigo == "ENTREGADO").first()
    pedido = db.query(Pedido).filter(Pedido.id == hi.pedido_id).first()
    if estado_entregado and pedido:
        pedido.estado_id = estado_entregado.id

    # Si todos los items están entregados → completar hoja de ruta
    todos_entregados = db.query(HojaRutaItem).filter(
        HojaRutaItem.hoja_ruta_id == hoja_id,
        HojaRutaItem.entregado == False,
        HojaRutaItem.id != item_id,
    ).count() == 0

    if todos_entregados:
        hoja.estado = EstadoHojaRuta.COMPLETADA
        if not hoja.fecha_retorno:
            hoja.fecha_retorno = datetime.now()

    db.commit()

    # Disparar webhook de entrega
    if pedido:
        trigger_pedido_entregado(pedido, db, fecha_entrega=hi.fecha_entrega)

    return {
        "ok": True,
        "item_id": item_id,
        "pedido_id": hi.pedido_id,
        "fecha_entrega": hi.fecha_entrega.isoformat(),
        "hoja_completada": todos_entregados,
    }


@router.post("/{hoja_id}/calcular-cobro-chofer")
def calcular_cobro_chofer(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Calcula y guarda el monto a cobrar al chofer.
    - FIJO: usa tarifa_chofer directamente.
    - POR_KG: tarifa_chofer × kg entregados efectivamente.
    """
    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id)
        .options(
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items).joinedload(ItemPedido.producto),
        )
        .first()
    )
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")
    if not hoja.tipo_cobro_chofer or hoja.tarifa_chofer is None:
        raise HTTPException(status_code=400, detail="No hay tipo de cobro o tarifa configurada")

    if hoja.tipo_cobro_chofer == "FIJO":
        monto = float(hoja.tarifa_chofer)
    else:  # POR_KG
        kg_entregados = sum(
            _kg_pedido(db, hi.pedido.items or [])
            for hi in (hoja.items or [])
            if hi.entregado and hi.pedido
        )
        monto = round(float(hoja.tarifa_chofer) * kg_entregados, 2)

    hoja.monto_cobro_chofer = monto
    db.commit()
    return {"ok": True, "monto_cobro_chofer": monto, "tipo_cobro_chofer": hoja.tipo_cobro_chofer}


@router.post("/{hoja_id}/pagar-chofer")
def pagar_chofer(
    hoja_id: int,
    body: PagarChoferRequest = PagarChoferRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Marca el cobro del chofer como pagado."""
    hoja = db.query(HojaRuta).filter(
        HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id
    ).first()
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")

    if body.monto is not None:
        hoja.monto_cobro_chofer = body.monto

    hoja.cobro_chofer_pagado = True
    hoja.fecha_pago_chofer = datetime.now()
    db.commit()
    return {
        "ok": True,
        "cobro_chofer_pagado": True,
        "monto_cobro_chofer": float(hoja.monto_cobro_chofer) if hoja.monto_cobro_chofer else None,
        "fecha_pago_chofer": hoja.fecha_pago_chofer.isoformat(),
    }


@router.post("/pagar-masivo")
def pagar_chofer_masivo(
    body: PagarChoferMasivoRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Liquida en una sola operación múltiples cobros pendientes a un chofer."""
    if not body.hoja_ids:
        raise HTTPException(status_code=400, detail="Debe indicar al menos una hoja de ruta")

    hojas = db.query(HojaRuta).filter(
        HojaRuta.id.in_(body.hoja_ids),
        HojaRuta.tenant_id == current_user.tenant_id,
        HojaRuta.cobro_chofer_pagado == False,
        HojaRuta.tipo_cobro_chofer.isnot(None),
    ).all()

    if not hojas:
        raise HTTPException(status_code=404, detail="No se encontraron rutas pendientes de pago")

    ahora = datetime.now()
    total = 0.0
    for hoja in hojas:
        hoja.cobro_chofer_pagado = True
        hoja.fecha_pago_chofer = ahora
        total += float(hoja.monto_cobro_chofer or 0)

    db.commit()
    return {
        "ok": True,
        "hojas_pagadas": len(hojas),
        "total_pagado": round(total, 2),
        "fecha_pago": ahora.isoformat(),
    }


@router.delete("/{hoja_id}")
def eliminar_hoja_ruta(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    hoja = db.query(HojaRuta).filter(
        HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id
    ).first()
    if not hoja:
        raise HTTPException(status_code=404, detail="Hoja de ruta no encontrada")
    if hoja.estado == EstadoHojaRuta.EN_RUTA:
        raise HTTPException(status_code=400, detail="No se puede eliminar una hoja de ruta EN_RUTA")

    db.delete(hoja)
    db.commit()
    return {"ok": True}
