"""
Router para Hojas de Ruta: agrupa pedidos confirmados en salidas de camión,
controla capacidad en kg y permite marcar entregas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.database import get_db
from database.models import (
    HojaRuta, HojaRutaItem, EstadoHojaRuta,
    Pedido, ItemPedido, AsignacionPicking,
    EstadoPedido, Cliente, Vehiculo, User,
)
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
    pedido_ids: List[int]


class HojaRutaUpdate(BaseModel):
    vehiculo_id: Optional[int] = None
    chofer_id: Optional[int] = None
    capacidad_kg: Optional[float] = None
    notas: Optional[str] = None
    estado: Optional[str] = None


class EntregarItemRequest(BaseModel):
    notas_entrega: Optional[str] = None


# ──────────────────────────────────────────
# Helper: kg brutos de un pedido
# ──────────────────────────────────────────

def _kg_pedido(db: Session, item_ids: List[int]) -> float:
    if not item_ids:
        return 0.0
    row = db.query(func.sum(AsignacionPicking.peso_real)).filter(
        AsignacionPicking.item_pedido_id.in_(item_ids)
    ).scalar()
    return float(row) if row else 0.0


def _build_pedido_summary(pedido: Pedido, db: Session) -> dict:
    item_ids = [i.id for i in pedido.items] if pedido.items else []
    kg = _kg_pedido(db, item_ids)
    return {
        "id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "cliente_nombre": pedido.cliente.nombre if pedido.cliente else None,
        "cliente_telefono": pedido.cliente.telefono if pedido.cliente else None,
        "direccion": pedido.cliente.direccion if pedido.cliente else None,
        "monto_total": float(pedido.monto_total) if pedido.monto_total else 0,
        "estado": pedido.estado_pedido.codigo if pedido.estado_pedido else None,
        "kg_brutos": kg,
        "items_count": len(pedido.items) if pedido.items else 0,
    }


def _build_hoja_response(hoja: HojaRuta, db: Session) -> dict:
    items_out = []
    total_kg = 0.0
    for hi in (hoja.items or []):
        pedido = hi.pedido
        if not pedido:
            continue
        pedido_data = _build_pedido_summary(pedido, db)
        total_kg += pedido_data["kg_brutos"]
        items_out.append({
            "id": hi.id,
            "pedido_id": hi.pedido_id,
            "orden": hi.orden,
            "entregado": hi.entregado,
            "fecha_entrega": hi.fecha_entrega.isoformat() if hi.fecha_entrega else None,
            "notas_entrega": hi.notas_entrega,
            "pedido": pedido_data,
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
    }


# ──────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────

@router.get("/pedidos-disponibles")
def listar_pedidos_disponibles(
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

    pedidos = (
        db.query(Pedido)
        .join(Cliente)
        .filter(
            Cliente.tenant_id == current_user.tenant_id,
            Pedido.estado_id == estado_confirmado.id,
            ~Pedido.id.in_(asignados_ids) if asignados_ids else True,
        )
        .options(
            joinedload(Pedido.cliente),
            joinedload(Pedido.items),
            joinedload(Pedido.estado_pedido),
        )
        .order_by(Pedido.fecha_pedido.desc())
        .all()
    )

    # Calcular kg por pedido en una sola consulta
    all_item_ids = [item.id for p in pedidos for item in (p.items or [])]
    peso_por_item: dict = {}
    if all_item_ids:
        rows = db.query(
            AsignacionPicking.item_pedido_id,
            func.sum(AsignacionPicking.peso_real).label("total_kg"),
        ).filter(
            AsignacionPicking.item_pedido_id.in_(all_item_ids)
        ).group_by(AsignacionPicking.item_pedido_id).all()
        peso_por_item = {r.item_pedido_id: float(r.total_kg) for r in rows}

    result = []
    for p in pedidos:
        kg = sum(peso_por_item.get(i.id, 0) for i in (p.items or []))
        result.append({
            "id": p.id,
            "numero_pedido": p.numero_pedido,
            "cliente_nombre": p.cliente.nombre if p.cliente else None,
            "cliente_telefono": p.cliente.telefono if p.cliente else None,
            "direccion": p.cliente.direccion if p.cliente else None,
            "monto_total": float(p.monto_total) if p.monto_total else 0,
            "kg_brutos": round(kg, 3),
            "items_count": len(p.items) if p.items else 0,
            "fecha_pedido": p.fecha_pedido.isoformat() if p.fecha_pedido else None,
        })
    return result


@router.post("/")
def crear_hoja_ruta(
    data: HojaRutaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea una hoja de ruta con los pedidos seleccionados."""
    if not data.pedido_ids:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un pedido")

    # Validar que los pedidos existen, son del tenant y están CONFIRMADOS
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
        .options(joinedload(Pedido.items))
        .all()
    )

    if len(pedidos) != len(data.pedido_ids):
        raise HTTPException(status_code=400, detail="Uno o más pedidos no son válidos o no están confirmados")

    # Verificar que no estén ya en una hoja de ruta
    ya_asignados = db.query(HojaRutaItem).filter(
        HojaRutaItem.pedido_id.in_(data.pedido_ids)
    ).first()
    if ya_asignados:
        raise HTTPException(status_code=400, detail="Uno o más pedidos ya están asignados a una hoja de ruta")

    # Calcular kg totales y validar capacidad
    all_item_ids = [item.id for p in pedidos for item in (p.items or [])]
    peso_por_item: dict = {}
    if all_item_ids:
        rows = db.query(
            AsignacionPicking.item_pedido_id,
            func.sum(AsignacionPicking.peso_real).label("total_kg"),
        ).filter(
            AsignacionPicking.item_pedido_id.in_(all_item_ids)
        ).group_by(AsignacionPicking.item_pedido_id).all()
        peso_por_item = {r.item_pedido_id: float(r.total_kg) for r in rows}

    total_kg = sum(
        sum(peso_por_item.get(item.id, 0) for item in (p.items or []))
        for p in pedidos
    )

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

    # Crear hoja de ruta
    hoja = HojaRuta(
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
        vehiculo_id=data.vehiculo_id,
        chofer_id=data.chofer_id,
        capacidad_kg=capacidad_efectiva,
        notas=data.notas,
        estado=EstadoHojaRuta.PENDIENTE,
    )
    db.add(hoja)
    db.flush()

    for orden, pedido_id in enumerate(data.pedido_ids):
        item = HojaRutaItem(
            hoja_ruta_id=hoja.id,
            pedido_id=pedido_id,
            orden=orden,
        )
        db.add(item)

    db.commit()
    db.refresh(hoja)

    # Recargar con relaciones
    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja.id)
        .options(
            joinedload(HojaRuta.vehiculo).joinedload(Vehiculo.tipo_vehiculo),
            joinedload(HojaRuta.chofer),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.cliente),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.estado_pedido),
        )
        .first()
    )
    return _build_hoja_response(hoja, db)


@router.get("/")
def listar_hojas_ruta(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista todas las hojas de ruta del tenant."""
    q = db.query(HojaRuta).filter(HojaRuta.tenant_id == current_user.tenant_id)
    if estado:
        q = q.filter(HojaRuta.estado == EstadoHojaRuta(estado))

    hojas = (
        q.options(
            joinedload(HojaRuta.vehiculo).joinedload(Vehiculo.tipo_vehiculo),
            joinedload(HojaRuta.chofer),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.cliente),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.estado_pedido),
        )
        .order_by(HojaRuta.fecha_creacion.desc())
        .all()
    )
    return [_build_hoja_response(h, db) for h in hojas]


@router.get("/{hoja_id}")
def obtener_hoja_ruta(
    hoja_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    hoja = (
        db.query(HojaRuta)
        .filter(HojaRuta.id == hoja_id, HojaRuta.tenant_id == current_user.tenant_id)
        .options(
            joinedload(HojaRuta.vehiculo).joinedload(Vehiculo.tipo_vehiculo),
            joinedload(HojaRuta.chofer),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.cliente),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.estado_pedido),
        )
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
        .options(
            joinedload(HojaRuta.vehiculo).joinedload(Vehiculo.tipo_vehiculo),
            joinedload(HojaRuta.chofer),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.cliente),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.items),
            joinedload(HojaRuta.items).joinedload(HojaRutaItem.pedido).joinedload(Pedido.estado_pedido),
        )
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
    if estado_entregado:
        pedido = db.query(Pedido).filter(Pedido.id == hi.pedido_id).first()
        if pedido:
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
    return {
        "ok": True,
        "item_id": item_id,
        "pedido_id": hi.pedido_id,
        "fecha_entrega": hi.fecha_entrega.isoformat(),
        "hoja_completada": todos_entregados,
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
