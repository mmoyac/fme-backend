"""
Router para gestión del sistema de despachos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import io

from database.database import get_db
from database.models import (
    Despacho, PickingItem, Pedido, ItemPedido, Cliente, Producto, 
    Local, User, EstadoDespacho, TipoPedido
)
from schemas.despacho import (
    DespachoCreate, DespachoUpdate, DespachoResponse, DespachoConPickingItems,
    AsignarDespachoRequest, IniciarPickingRequest, CompletarPickingItemRequest,
    IniciarRutaRequest, ActualizarUbicacionRequest, ConfirmarEntregaRequest,
    PickingItemUpdate, PickingItemResponse, ResumenDespachoResponse,
    NotaPickingResponse, EscanearCodigoBarrasRequest, EscanearCodigoBarrasResponse
)
from routers.auth import get_current_active_user

router = APIRouter()


# ============================================
# ENDPOINTS DE GESTIÓN DE DESPACHOS
# ============================================

@router.get("/", response_model=List[DespachoResponse])
def listar_despachos(
    skip: int = 0,
    limit: int = 50,
    estado: str = None,
    despachador_id: int = None,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar despachos con filtros."""
    query = db.query(Despacho).options(
        joinedload(Despacho.pedido).joinedload(Pedido.cliente),
        joinedload(Despacho.despachador)
    )
    
    # Aplicar filtros
    if estado:
        query = query.filter(Despacho.estado_despacho == estado)
    if despachador_id:
        query = query.filter(Despacho.despachador_user_id == despachador_id)
    if fecha_desde:
        query = query.filter(Despacho.fecha_asignacion >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Despacho.fecha_asignacion <= fecha_hasta)
    
    # Ordenar por fecha más reciente
    query = query.order_by(desc(Despacho.fecha_asignacion))
    
    despachos = query.offset(skip).limit(limit).all()
    
    # Construir respuesta con información adicional
    result = []
    for despacho in despachos:
        despacho_dict = {
            "id": despacho.id,
            "pedido_id": despacho.pedido_id,
            "despachador_user_id": despacho.despachador_user_id,
            "estado_despacho": despacho.estado_despacho,
            "fecha_asignacion": despacho.fecha_asignacion,
            "fecha_inicio_picking": despacho.fecha_inicio_picking,
            "fecha_fin_picking": despacho.fecha_fin_picking,
            "fecha_inicio_ruta": despacho.fecha_inicio_ruta,
            "fecha_entrega": despacho.fecha_entrega,
            "notas_despacho": despacho.notas_despacho,
            "ubicacion_actual": despacho.ubicacion_actual,
            "hora_estimada_entrega": despacho.hora_estimada_entrega,
            "despachador_nombre": despacho.despachador.nombre_completo if despacho.despachador else None,
            "pedido_numero": f"#{despacho.pedido.id}",
            "pedido_total": float(despacho.pedido.monto_total) if despacho.pedido else None,
            "cliente_nombre": despacho.pedido.cliente.nombre if despacho.pedido and despacho.pedido.cliente else None,
            "direccion_entrega": despacho.pedido.notas if despacho.pedido else None  # Asumiendo que la dirección está en notas
        }
        result.append(DespachoResponse(**despacho_dict))
    
    return result


@router.get("/{despacho_id}", response_model=DespachoConPickingItems)
def obtener_despacho(
    despacho_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener despacho específico con items de picking."""
    despacho = db.query(Despacho).options(
        joinedload(Despacho.pedido).joinedload(Pedido.cliente),
        joinedload(Despacho.pedido).joinedload(Pedido.items).joinedload(ItemPedido.producto),
        joinedload(Despacho.despachador),
        joinedload(Despacho.picking_items).joinedload(PickingItem.item_pedido).joinedload(ItemPedido.producto)
    ).filter(Despacho.id == despacho_id).first()
    
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    # Construir respuesta
    picking_items = []
    for picking_item in despacho.picking_items:
        item_dict = {
            "id": picking_item.id,
            "despacho_id": picking_item.despacho_id,
            "item_pedido_id": picking_item.item_pedido_id,
            "usuario_picking_id": picking_item.usuario_picking_id,
            "cantidad_solicitada": picking_item.cantidad_solicitada,
            "cantidad_pickeada": picking_item.cantidad_pickeada,
            "lote_codigo": picking_item.lote_codigo,
            "peso_solicitado": picking_item.peso_solicitado,
            "peso_real": picking_item.peso_real,
            "fecha_vencimiento": picking_item.fecha_vencimiento,
            "ubicacion_picking": picking_item.ubicacion_picking,
            "codigo_barras_escaneado": picking_item.codigo_barras_escaneado,
            "fecha_picking": picking_item.fecha_picking,
            "notas_picking": picking_item.notas_picking,
            "completado": picking_item.completado,
            "producto_sku": picking_item.item_pedido.producto.sku if picking_item.item_pedido and picking_item.item_pedido.producto else None,
            "producto_nombre": picking_item.item_pedido.producto.nombre if picking_item.item_pedido and picking_item.item_pedido.producto else None
        }
        picking_items.append(PickingItemResponse(**item_dict))
    
    despacho_dict = {
        "id": despacho.id,
        "pedido_id": despacho.pedido_id,
        "despachador_user_id": despacho.despachador_user_id,
        "estado_despacho": despacho.estado_despacho,
        "fecha_asignacion": despacho.fecha_asignacion,
        "fecha_inicio_picking": despacho.fecha_inicio_picking,
        "fecha_fin_picking": despacho.fecha_fin_picking,
        "fecha_inicio_ruta": despacho.fecha_inicio_ruta,
        "fecha_entrega": despacho.fecha_entrega,
        "notas_despacho": despacho.notas_despacho,
        "ubicacion_actual": despacho.ubicacion_actual,
        "hora_estimada_entrega": despacho.hora_estimada_entrega,
        "despachador_nombre": despacho.despachador.nombre_completo if despacho.despachador else None,
        "pedido_numero": f"#{despacho.pedido.id}",
        "pedido_total": float(despacho.pedido.monto_total) if despacho.pedido else None,
        "cliente_nombre": despacho.pedido.cliente.nombre if despacho.pedido and despacho.pedido.cliente else None,
        "direccion_entrega": despacho.pedido.notas if despacho.pedido else None,
        "picking_items": picking_items
    }
    
    return DespachoConPickingItems(**despacho_dict)


@router.post("/asignar/{pedido_id}", response_model=DespachoResponse)
def asignar_despacho(
    pedido_id: int,
    despacho_data: AsignarDespachoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Asignar despacho a un pedido confirmado."""
    # Verificar que el pedido existe y está en estado CONFIRMADO
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    if pedido.estado != "CONFIRMADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden asignar despachos a pedidos confirmados"
        )
    
    # Verificar que no existe ya un despacho para este pedido
    despacho_existente = db.query(Despacho).filter(Despacho.pedido_id == pedido_id).first()
    if despacho_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido ya tiene un despacho asignado"
        )
    
    # Verificar que el despachador existe
    despachador = db.query(User).filter(User.id == despacho_data.despachador_user_id).first()
    if not despachador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despachador no encontrado"
        )
    
    # Crear el despacho
    despacho = Despacho(
        pedido_id=pedido_id,
        despachador_user_id=despacho_data.despachador_user_id,
        estado_despacho=EstadoDespacho.ASIGNADO,
        notas_despacho=despacho_data.notas_despacho,
        hora_estimada_entrega=despacho_data.hora_estimada_entrega
    )
    
    db.add(despacho)
    db.flush()  # Para obtener el ID
    
    # Crear picking items para cada item del pedido
    items_pedido = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido_id).all()
    
    for item in items_pedido:
        # Determinar si es producto regular o caja variable
        es_caja_variable = pedido.tipo_pedido and pedido.tipo_pedido.codigo == "CAJAS_VARIABLES"
        
        picking_item = PickingItem(
            despacho_id=despacho.id,
            item_pedido_id=item.id,
            cantidad_solicitada=item.cantidad if not es_caja_variable else None,
            peso_solicitado=float(item.precio_unitario) if es_caja_variable else None  # Asumir que precio_unitario contiene el peso estimado para cajas
        )
        
        db.add(picking_item)
    
    db.commit()
    db.refresh(despacho)
    
    # Actualizar el estado del pedido
    pedido.estado = "EN_PREPARACION"
    db.commit()
    
    # Preparar respuesta
    despacho_dict = {
        "id": despacho.id,
        "pedido_id": despacho.pedido_id,
        "despachador_user_id": despacho.despachador_user_id,
        "estado_despacho": despacho.estado_despacho,
        "fecha_asignacion": despacho.fecha_asignacion,
        "fecha_inicio_picking": despacho.fecha_inicio_picking,
        "fecha_fin_picking": despacho.fecha_fin_picking,
        "fecha_inicio_ruta": despacho.fecha_inicio_ruta,
        "fecha_entrega": despacho.fecha_entrega,
        "notas_despacho": despacho.notas_despacho,
        "ubicacion_actual": despacho.ubicacion_actual,
        "hora_estimada_entrega": despacho.hora_estimada_entrega,
        "despachador_nombre": despachador.nombre_completo,
        "pedido_numero": f"#{pedido.id}",
        "pedido_total": float(pedido.monto_total),
        "cliente_nombre": pedido.cliente.nombre if pedido.cliente else None,
        "direccion_entrega": pedido.notas
    }
    
    return DespachoResponse(**despacho_dict)


# ============================================
# ENDPOINTS DE PROCESO DE PICKING
# ============================================

@router.post("/{despacho_id}/iniciar-picking", response_model=DespachoResponse)
def iniciar_picking(
    despacho_id: int,
    picking_data: IniciarPickingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Iniciar proceso de picking para un despacho."""
    despacho = db.query(Despacho).filter(Despacho.id == despacho_id).first()
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    if despacho.estado_despacho != EstadoDespacho.ASIGNADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede iniciar picking en despachos asignados"
        )
    
    # Actualizar estado y timestamps
    despacho.estado_despacho = EstadoDespacho.EN_PICKING
    despacho.fecha_inicio_picking = datetime.now()
    if picking_data.ubicacion_actual:
        despacho.ubicacion_actual = picking_data.ubicacion_actual
    if picking_data.notas_despacho:
        despacho.notas_despacho = picking_data.notas_despacho
    
    db.commit()
    db.refresh(despacho)
    
    return obtener_despacho(despacho_id, db, current_user)


@router.put("/picking-item/{picking_item_id}")
def actualizar_picking_item(
    picking_item_id: int,
    picking_update: CompletarPickingItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar item de picking (completar picking de un producto)."""
    picking_item = db.query(PickingItem).filter(PickingItem.id == picking_item_id).first()
    if not picking_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Picking item con ID {picking_item_id} no encontrado"
        )
    
    # Actualizar campos
    if picking_update.cantidad_pickeada is not None:
        picking_item.cantidad_pickeada = picking_update.cantidad_pickeada
    if picking_update.peso_real is not None:
        picking_item.peso_real = picking_update.peso_real
    if picking_update.ubicacion_picking:
        picking_item.ubicacion_picking = picking_update.ubicacion_picking
    if picking_update.codigo_barras_escaneado:
        picking_item.codigo_barras_escaneado = picking_update.codigo_barras_escaneado
    if picking_update.notas_picking:
        picking_item.notas_picking = picking_update.notas_picking
    
    # Marcar como completado si se pickeó la cantidad/peso correcto
    if picking_update.cantidad_pickeada and picking_update.cantidad_pickeada > 0:
        picking_item.completado = True
    elif picking_update.peso_real and picking_update.peso_real > 0:
        picking_item.completado = True
    
    picking_item.usuario_picking_id = current_user.id
    picking_item.fecha_picking = datetime.now()
    
    db.commit()
    
    return {"message": "Picking item actualizado correctamente"}


@router.post("/{despacho_id}/completar-picking", response_model=DespachoResponse)
def completar_picking(
    despacho_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Completar proceso de picking cuando todos los items están listos."""
    despacho = db.query(Despacho).filter(Despacho.id == despacho_id).first()
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    if despacho.estado_despacho != EstadoDespacho.EN_PICKING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede completar picking en despachos que están en proceso de picking"
        )
    
    # Verificar que todos los items están completados
    items_pendientes = db.query(PickingItem).filter(
        and_(
            PickingItem.despacho_id == despacho_id,
            PickingItem.completado == False
        )
    ).count()
    
    if items_pendientes > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aún hay {items_pendientes} items pendientes de picking"
        )
    
    # Actualizar estado
    despacho.estado_despacho = EstadoDespacho.LISTO_EMPAQUE
    despacho.fecha_fin_picking = datetime.now()
    
    db.commit()
    
    return obtener_despacho(despacho_id, db, current_user)


# ============================================
# ENDPOINTS DE RUTA Y ENTREGA
# ============================================

@router.post("/{despacho_id}/iniciar-ruta", response_model=DespachoResponse)
def iniciar_ruta(
    despacho_id: int,
    ruta_data: IniciarRutaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Iniciar ruta de entrega."""
    despacho = db.query(Despacho).filter(Despacho.id == despacho_id).first()
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    if despacho.estado_despacho != EstadoDespacho.LISTO_EMPAQUE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede iniciar ruta con despachos listos para empaque"
        )
    
    despacho.estado_despacho = EstadoDespacho.EN_RUTA
    despacho.fecha_inicio_ruta = datetime.now()
    despacho.ubicacion_actual = ruta_data.ubicacion_actual
    if ruta_data.hora_estimada_entrega:
        despacho.hora_estimada_entrega = ruta_data.hora_estimada_entrega
    
    db.commit()
    
    return obtener_despacho(despacho_id, db, current_user)


@router.put("/{despacho_id}/ubicacion")
def actualizar_ubicacion(
    despacho_id: int,
    ubicacion_data: ActualizarUbicacionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar ubicación del despachador en ruta."""
    despacho = db.query(Despacho).filter(Despacho.id == despacho_id).first()
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    despacho.ubicacion_actual = ubicacion_data.ubicacion_actual
    if ubicacion_data.hora_estimada_entrega:
        despacho.hora_estimada_entrega = ubicacion_data.hora_estimada_entrega
    
    db.commit()
    
    return {"message": "Ubicación actualizada correctamente"}


@router.post("/{despacho_id}/confirmar-entrega", response_model=DespachoResponse)
def confirmar_entrega(
    despacho_id: int,
    entrega_data: ConfirmarEntregaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Confirmar entrega del pedido."""
    despacho = db.query(Despacho).filter(Despacho.id == despacho_id).first()
    if not despacho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Despacho con ID {despacho_id} no encontrado"
        )
    
    if despacho.estado_despacho != EstadoDespacho.EN_RUTA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede confirmar entrega de despachos en ruta"
        )
    
    # Actualizar despacho
    despacho.estado_despacho = EstadoDespacho.ENTREGADO
    despacho.fecha_entrega = datetime.now()
    despacho.ubicacion_actual = entrega_data.ubicacion_entrega
    if entrega_data.notas_entrega:
        if despacho.notas_despacho:
            despacho.notas_despacho += f"\\n\\nEntrega: {entrega_data.notas_entrega}"
        else:
            despacho.notas_despacho = f"Entrega: {entrega_data.notas_entrega}"
    
    # Actualizar estado del pedido
    pedido = db.query(Pedido).filter(Pedido.id == despacho.pedido_id).first()
    if pedido:
        pedido.estado = "ENTREGADO"
    
    db.commit()
    
    return obtener_despacho(despacho_id, db, current_user)


# ============================================
# ENDPOINTS DE REPORTES Y UTILIDADES
# ============================================

@router.get("/resumen", response_model=ResumenDespachoResponse)
def obtener_resumen_despachos(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener resumen de despachos."""
    query_base = db.query(Despacho)
    
    if fecha_desde:
        query_base = query_base.filter(Despacho.fecha_asignacion >= fecha_desde)
    if fecha_hasta:
        query_base = query_base.filter(Despacho.fecha_asignacion <= fecha_hasta)
    
    total_despachos = query_base.count()
    en_picking = query_base.filter(Despacho.estado_despacho == EstadoDespacho.EN_PICKING).count()
    listos_empaque = query_base.filter(Despacho.estado_despacho == EstadoDespacho.LISTO_EMPAQUE).count()
    en_ruta = query_base.filter(Despacho.estado_despacho == EstadoDespacho.EN_RUTA).count()
    
    # Entregados hoy
    hoy = datetime.now().date()
    entregados_hoy = query_base.filter(
        and_(
            Despacho.estado_despacho == EstadoDespacho.ENTREGADO,
            func.date(Despacho.fecha_entrega) == hoy
        )
    ).count()
    
    return ResumenDespachoResponse(
        total_despachos=total_despachos,
        en_picking=en_picking,
        listos_empaque=listos_empaque,
        en_ruta=en_ruta,
        entregados_hoy=entregados_hoy
    )