"""
Router para endpoints de Pedidos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Pedido, ItemPedido, Cliente, Producto, Local, Inventario, MovimientoInventario
from schemas.pedido import (
    PedidoCreateFrontend,
    PedidoConfirmacion,
    PedidoResponse,
    PedidoConRelaciones,
    PedidoUpdate,
    EstadoPedido
)

from routers.auth import get_current_active_user

router = APIRouter()


def descontar_inventario(pedido: Pedido, local_despacho_id: int, db: Session):
    """
    Descuenta el inventario de los productos del pedido.
    
    Args:
        pedido: El pedido del cual descontar inventario
        local_despacho_id: ID del local desde donde se despacha
        db: Sesión de base de datos
    
    Raises:
        HTTPException: Si no hay suficiente stock
    """
    # Verificar que no se haya descontado antes
    if pedido.inventario_descontado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El inventario ya fue descontado para este pedido"
        )
    
    # Validar stock antes de descontar
    for item in pedido.items:
        inventario = db.query(Inventario).filter(
            Inventario.producto_id == item.producto_id,
            Inventario.local_id == local_despacho_id
        ).first()
        
        if not inventario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto {item.producto.nombre} no tiene inventario en el local seleccionado"
            )
        
        if inventario.cantidad_stock < item.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {item.producto.nombre}. Disponible: {inventario.cantidad_stock}, Requerido: {item.cantidad}"
            )
    
    # Si pasó la validación, descontar
    for item in pedido.items:
        inventario = db.query(Inventario).filter(
            Inventario.producto_id == item.producto_id,
            Inventario.local_id == local_despacho_id
        ).first()
        
        inventario.cantidad_stock -= item.cantidad
        
        # Registrar movimiento
        movimiento = MovimientoInventario(
            producto_id=item.producto_id,
            local_origen_id=local_despacho_id,
            local_destino_id=None,  # NULL = salida por pedido
            cantidad=item.cantidad,
            tipo_movimiento="PEDIDO",
            referencia_id=pedido.id,
            notas=f"Descuento por pedido #{pedido.id}",
            usuario="sistema"
        )
        db.add(movimiento)
    
    # Marcar como descontado
    pedido.inventario_descontado = True
    pedido.local_despacho_id = local_despacho_id


def devolver_inventario(pedido: Pedido, db: Session):
    """
    Devuelve el inventario al cancelar un pedido.
    
    Args:
        pedido: El pedido del cual devolver inventario
        db: Sesión de base de datos
    """
    if not pedido.inventario_descontado or not pedido.local_despacho_id:
        return  # No hay nada que devolver
    
    for item in pedido.items:
        inventario = db.query(Inventario).filter(
            Inventario.producto_id == item.producto_id,
            Inventario.local_id == pedido.local_despacho_id
        ).first()
        
        if inventario:
            inventario.cantidad_stock += item.cantidad
            
            # Registrar movimiento de devolución
            movimiento = MovimientoInventario(
                producto_id=item.producto_id,
                local_origen_id=None,  # NULL = entrada por devolución
                local_destino_id=pedido.local_despacho_id,
                cantidad=item.cantidad,
                tipo_movimiento="AJUSTE",
                referencia_id=pedido.id,
                notas=f"Devolución por cancelación de pedido #{pedido.id}",
                usuario="sistema"
            )
            db.add(movimiento)
    
    pedido.inventario_descontado = False


@router.post("/", response_model=PedidoConfirmacion, status_code=status.HTTP_201_CREATED)
def crear_pedido_frontend(pedido_data: PedidoCreateFrontend, db: Session = Depends(get_db)):
    """
    Crea un nuevo pedido desde el frontend (sin autenticación).
    
    **Flujo:**
    1. Busca o crea el cliente con el email
    2. Valida que los productos existan y tengan precio en local WEB
    3. Crea el pedido con estado PENDIENTE
    4. Crea los items del pedido
    5. Calcula el monto total
    
    **Uso:** Landing - Checkout del carrito
    """
    # 1. Buscar local WEB
    local_web = db.query(Local).filter(Local.codigo == 'WEB').first()
    if not local_web:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Local WEB no configurado en el sistema"
        )
    
    # 2. Buscar o crear cliente
    cliente = db.query(Cliente).filter(Cliente.email == pedido_data.cliente_email).first()
    
    if not cliente:
        # Crear nuevo cliente
        cliente = Cliente(
            nombre=pedido_data.cliente_nombre,
            apellido=pedido_data.cliente_apellido,
            email=pedido_data.cliente_email,
            telefono=pedido_data.cliente_telefono,
            direccion=pedido_data.direccion_entrega,
            comuna=pedido_data.comuna
        )
        db.add(cliente)
        db.flush()  # Para obtener el ID sin hacer commit
    else:
        # Actualizar datos del cliente existente
        cliente.nombre = pedido_data.cliente_nombre
        cliente.apellido = pedido_data.cliente_apellido
        cliente.telefono = pedido_data.cliente_telefono
        cliente.direccion = pedido_data.direccion_entrega
        cliente.comuna = pedido_data.comuna
    
    # 3. Validar productos y calcular total
    items_a_crear = []
    monto_total = 0.0
    
    for item_data in pedido_data.items:
        # Buscar producto por SKU
        producto = db.query(Producto).filter(Producto.sku == item_data.sku).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con SKU {item_data.sku} no encontrado"
            )
        
        # Obtener precio del producto para el local WEB
        from database.models import Precio
        precio = db.query(Precio).filter(
            Precio.producto_id == producto.id,
            Precio.local_id == local_web.id
        ).first()
        
        if not precio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto {producto.nombre} no tiene precio configurado"
            )
        
        # Preparar item
        items_a_crear.append({
            'producto_id': producto.id,
            'cantidad': item_data.cantidad,
            'precio_unitario_venta': precio.monto_precio
        })
        
        monto_total += precio.monto_precio * item_data.cantidad
    
    # 4. Crear pedido
    db_pedido = Pedido(
        cliente_id=cliente.id,
        local_id=local_web.id,
        monto_total=monto_total,
        estado="PENDIENTE",
        es_pagado=False,
        notas=pedido_data.notas
    )
    db.add(db_pedido)
    db.flush()  # Para obtener el ID
    
    # 5. Crear items del pedido
    for item_info in items_a_crear:
        item = ItemPedido(
            pedido_id=db_pedido.id,
            **item_info
        )
        db.add(item)
    
    db.commit()
    db.refresh(db_pedido)
    
    # 6. Retornar confirmación
    return PedidoConfirmacion(
        pedido_id=db_pedido.id,
        numero_pedido=f"PED-{db_pedido.id:05d}",
        monto_total=monto_total,
        estado=db_pedido.estado,
        mensaje="¡Pedido recibido! Te contactaremos pronto para coordinar el pago y entrega."
    )


@router.get("/", response_model=List[PedidoConRelaciones])
def listar_pedidos(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los pedidos con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de pedidos
    """
    query = db.query(Pedido)
    
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.order_by(Pedido.fecha_pedido.desc()).offset(skip).limit(limit).all()
    
    # Mapear a schema de respuesta
    result = []
    for pedido in pedidos:
        pedido_dict = {
            'id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'local_id': pedido.local_id,
            'local_despacho_id': pedido.local_despacho_id,
            'numero_pedido': f"PED-{pedido.id:05d}",
            'fecha_pedido': pedido.fecha_pedido,
            'total': pedido.monto_total,
            'estado': pedido.estado,
            'pagado': pedido.es_pagado,
            'inventario_descontado': pedido.inventario_descontado,
            'notas': pedido.notas,
            'notas_admin': pedido.notas_admin,
            'cliente': pedido.cliente,
            'items': pedido.items
        }
        result.append(pedido_dict)
    
    return result


@router.get("/{pedido_id}", response_model=PedidoConRelaciones)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Obtiene un pedido por ID.
    
    **Uso:** Backoffice - Detalle de pedido
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    # Mapear a schema de respuesta
    return {
        'id': pedido.id,
        'cliente_id': pedido.cliente_id,
        'local_id': pedido.local_id,
        'numero_pedido': f"PED-{pedido.id:05d}",
        'fecha_pedido': pedido.fecha_pedido,
        'total': pedido.monto_total,
        'estado': pedido.estado,
        'pagado': pedido.es_pagado,
        'notas': pedido.notas,
        'notas_admin': pedido.notas_admin,
        'cliente': pedido.cliente,
        'items': pedido.items
    }


@router.put("/{pedido_id}", response_model=PedidoConRelaciones)
def actualizar_pedido(
    pedido_id: int,
    pedido_update: PedidoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza el estado de un pedido y gestiona el inventario.
    
    **Lógica de inventario:**
    - Si cambia a CONFIRMADO y se proporciona local_despacho_id → Descuenta inventario
    - Si cambia a CANCELADO y había inventario descontado → Devuelve inventario
    
    **Uso:** Backoffice - Cambiar estado del pedido
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    estado_anterior = pedido.estado
    
    # Actualizar campos básicos
    if pedido_update.pagado is not None:
        pedido.es_pagado = pedido_update.pagado
    if pedido_update.notas_admin is not None:
        pedido.notas_admin = pedido_update.notas_admin
    
    # Gestión de inventario según cambio de estado
    if pedido_update.estado:
        nuevo_estado = pedido_update.estado.value
        
        # Si cambia a CONFIRMADO
        if nuevo_estado == "CONFIRMADO" and estado_anterior != "CONFIRMADO":
            if not pedido_update.local_despacho_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe seleccionar un local de despacho para confirmar el pedido"
                )
            
            # Descontar inventario
            descontar_inventario(pedido, pedido_update.local_despacho_id, db)
        
        # Si cambia a CANCELADO
        elif nuevo_estado == "CANCELADO" and estado_anterior != "CANCELADO":
            # Devolver inventario si había sido descontado
            devolver_inventario(pedido, db)
        
        pedido.estado = nuevo_estado
    
    # Si solo se actualiza el local de despacho sin cambiar estado (caso raro pero posible)
    elif pedido_update.local_despacho_id and pedido.estado == "CONFIRMADO" and not pedido.inventario_descontado:
        descontar_inventario(pedido, pedido_update.local_despacho_id, db)
    
    db.commit()
    db.refresh(pedido)
    
    # Mapear a schema de respuesta
    return {
        'id': pedido.id,
        'cliente_id': pedido.cliente_id,
        'local_id': pedido.local_id,
        'local_despacho_id': pedido.local_despacho_id,
        'numero_pedido': f"PED-{pedido.id:05d}",
        'fecha_pedido': pedido.fecha_pedido,
        'total': pedido.monto_total,
        'estado': pedido.estado,
        'pagado': pedido.es_pagado,
        'inventario_descontado': pedido.inventario_descontado,
        'notas': pedido.notas,
        'notas_admin': pedido.notas_admin,
        'cliente': pedido.cliente,
        'items': pedido.items
    }
