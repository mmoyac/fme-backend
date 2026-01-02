"""
Router para endpoints de Pedidos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import io
from decimal import Decimal

from database.database import get_db
from database.models import Pedido, ItemPedido, Cliente, Producto, Local, Inventario, MovimientoInventario, TurnoCaja, OperacionCaja, TipoOperacionCaja, EstadoTurnoCaja
from schemas.pedido import (
    PedidoCreateFrontend,
    PedidoCreateBackoffice,
    PedidoConfirmacion,
    PedidoResponse,
    PedidoConRelaciones,
    PedidoUpdate,
    EstadoPedido
)

from routers.auth import get_current_active_user
from services.boleta_service import generar_boleta_pedido
from services.credito_service import CreditoService
from services.puntos_service import PuntosService

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


def registrar_venta_en_caja(pedido: Pedido, usuario_actual_id: int, db: Session):
    """
    Registra automáticamente una operación de venta en el turno de caja activo del vendedor.
    
    IMPORTANTE: Solo para locales físicos. Las ventas de Tienda Online (código='WEB') 
    no se registran en caja física.
    
    Args:
        pedido: El pedido confirmado
        usuario_actual_id: ID del usuario que confirma el pedido
        db: Sesión de base de datos
    """
    # Verificar que no sea una venta online (código WEB)
    if pedido.local_despacho and hasattr(pedido.local_despacho, 'codigo'):
        if pedido.local_despacho.codigo == 'WEB':
            # Las ventas online no pasan por caja física
            return
    
    # Buscar turno activo del vendedor en el local de despacho
    turno_activo = db.query(TurnoCaja).filter(
        TurnoCaja.vendedor_id == usuario_actual_id,
        TurnoCaja.local_id == pedido.local_despacho_id,
        TurnoCaja.estado == "ABIERTO"
    ).first()
    
    if not turno_activo:
        # Si no hay turno activo, no registramos venta automática
        # (podría ser un admin confirmando pedidos sin estar en caja)
        return
    
    # Crear operación de venta
    operacion = OperacionCaja(
        turno_caja_id=turno_activo.id,
        tipo_operacion=TipoOperacionCaja.VENTA,
        monto=pedido.monto_total,
        descripcion=f"Venta - Pedido #{pedido.id}",
        observaciones=f"Venta automática por confirmación de pedido #{pedido.id} - Cliente: {pedido.cliente.nombre if pedido.cliente else 'N/A'}",
        pedido_id=pedido.id,
        medio_pago_id=pedido.medio_pago_id
    )
    
    db.add(operacion)
    
    # Los totales se calculan dinámicamente desde las operaciones,
    # por lo que no necesitamos actualizar campos en TurnoCaja


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

    # 1.5. Buscar medio de pago por código
    from database.models import MedioPago
    medio_pago = None
    if pedido_data.medio_pago_codigo:
        medio_pago = db.query(MedioPago).filter(MedioPago.codigo == pedido_data.medio_pago_codigo).first()
        if not medio_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medio de pago '{pedido_data.medio_pago_codigo}' no encontrado"
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
    
    # 3.5. Procesar uso de puntos si se especificó
    descuento_puntos = 0.0
    puntos_usar = pedido_data.puntos_usar or 0
    
    if puntos_usar > 0:
        # Validar que el cliente tenga suficientes puntos
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        
        valido, mensaje, descuento = PuntosService.validar_uso_puntos_en_total(
            puntos_cliente.puntos_disponibles,
            puntos_usar,
            Decimal(str(monto_total))
        )
        
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )
        
        descuento_puntos = float(descuento)
        monto_total -= descuento_puntos  # Aplicar descuento al total
        
        if monto_total < 0:
            monto_total = 0
    
    # 4. Crear pedido
    db_pedido = Pedido(
        cliente_id=cliente.id,
        local_id=local_web.id,
        medio_pago_id=medio_pago.id if medio_pago else None,
        monto_total=monto_total,
        estado="PENDIENTE",
        es_pagado=False,
        notas=pedido_data.notas,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos
    )
    db.add(db_pedido)
    db.flush()  # Para obtener el ID
    
    # 5. Crear items del pedido PRIMERO
    for item_info in items_a_crear:
        item = ItemPedido(
            pedido_id=db_pedido.id,
            **item_info
        )
        db.add(item)
    
    # 5.5. DESPUÉS calcular puntos que se ganarían (ahora que los items existen)
    puntos_ganados = PuntosService.calcular_puntos_por_pedido(db, db_pedido.id)
    db_pedido.puntos_ganados = puntos_ganados
    
    # 6. Usar puntos si se especificó
    if puntos_usar > 0:
        exito, mensaje_puntos, movimiento = PuntosService.usar_puntos_en_pedido(
            db, cliente.id, db_pedido.id, puntos_usar, Decimal(str(descuento_puntos))
        )
        
        if not exito:
            # Rollback y error
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al usar puntos: {mensaje_puntos}"
            )
    
    db.commit()
    db.refresh(db_pedido)
    
    # 6. Retornar confirmación
    return PedidoConfirmacion(
        pedido_id=db_pedido.id,
        numero_pedido=f"PED-{db_pedido.id:05d}",
        monto_total=monto_total,
        estado=db_pedido.estado,
        mensaje="¡Pedido recibido! Te contactaremos pronto para coordinar el pago y entrega.",
        puntos_ganados=puntos_ganados,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos
    )


@router.post("/backoffice", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_pedido_backoffice(
    pedido_data: PedidoCreateBackoffice, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Crea un nuevo pedido desde el backoffice.
    
    **Flujo:**
    1. Valida que el cliente, local y medio de pago existan
    2. Valida que todos los productos existan
    3. Crea el pedido con estado PENDIENTE
    4. Crea los items del pedido con los precios especificados
    5. Calcula el monto total
    
    **Uso:** Backoffice - Crear pedido manual
    """
    # 1. Validar que el cliente exista
    cliente = db.query(Cliente).filter(Cliente.id == pedido_data.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {pedido_data.cliente_id} no encontrado"
        )
    
    # 2. Validar que el local exista
    local = db.query(Local).filter(Local.id == pedido_data.local_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {pedido_data.local_id} no encontrado"
        )
    
    # 3. Validar que el medio de pago exista
    from database.models import MedioPago
    medio_pago = db.query(MedioPago).filter(MedioPago.id == pedido_data.medio_pago_id).first()
    if not medio_pago:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Medio de pago con ID {pedido_data.medio_pago_id} no encontrado"
        )
    
    # 4. Validar productos y calcular total
    items_a_crear = []
    monto_total = 0.0
    
    for item_data in pedido_data.items:
        # Buscar producto por ID
        producto = db.query(Producto).filter(Producto.id == item_data.producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {item_data.producto_id} no encontrado"
            )
        
        # Verificar que el SKU coincida
        if producto.sku != item_data.sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU no coincide para el producto {item_data.producto_id}"
            )
        
        # Preparar item
        items_a_crear.append({
            'producto_id': producto.id,
            'cantidad': item_data.cantidad,
            'precio_unitario_venta': item_data.precio_unitario_venta
        })
        
        monto_total += item_data.precio_unitario_venta * item_data.cantidad
    
    # 4.3. Procesar uso de puntos si se especificó
    descuento_puntos = 0.0
    puntos_usar = pedido_data.puntos_usar or 0
    
    if puntos_usar > 0:
        # Validar que el cliente tenga suficientes puntos
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        
        valido, mensaje, descuento = PuntosService.validar_uso_puntos_en_total(
            puntos_cliente.puntos_disponibles,
            puntos_usar,
            Decimal(str(monto_total))
        )
        
        if not valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )
        
        descuento_puntos = float(descuento)
        monto_total -= descuento_puntos  # Aplicar descuento al total
        
        if monto_total < 0:
            monto_total = 0
    
    # 4.5. Validar crédito si el medio de pago permite cheques
    if medio_pago.permite_cheque:
        es_valido, mensaje = CreditoService.validar_credito_disponible(
            cliente.id, monto_total, db
        )
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )
    
    # 5. Crear pedido
    db_pedido = Pedido(
        cliente_id=cliente.id,
        local_id=local.id,
        medio_pago_id=medio_pago.id,
        monto_total=monto_total,
        estado="PENDIENTE",
        es_pagado=False,
        notas=pedido_data.notas,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos
    )
    db.add(db_pedido)
    db.flush()  # Para obtener el ID
    
    # 6. Crear items del pedido PRIMERO
    for item_info in items_a_crear:
        item = ItemPedido(
            pedido_id=db_pedido.id,
            **item_info
        )
        db.add(item)
    
    # 6.5. DESPUÉS calcular puntos que se ganarían (ahora que los items existen)
    puntos_ganados = PuntosService.calcular_puntos_por_pedido(db, db_pedido.id)
    db_pedido.puntos_ganados = puntos_ganados
    
    # NOTA: Los puntos NO se usan aquí, solo cuando se confirma el pedido
    # Esto garantiza que los pedidos PENDIENTE no descuenten puntos del cliente
    # Los puntos se usarán en el endpoint de actualizar_estado_pedido cuando estado = 'CONFIRMADO'
    
    db.commit()
    db.refresh(db_pedido)
    
    # 6.5. Ocupar crédito si el medio de pago permite cheques
    if medio_pago.permite_cheque:
        CreditoService.ocupar_credito(cliente.id, monto_total, db)
    
    # 7. Retornar respuesta
    return {
        "pedido_id": db_pedido.id,
        "numero_pedido": f"PED-{db_pedido.id:05d}",
        "monto_total": monto_total,
        "estado": db_pedido.estado,
        "mensaje": f"Pedido creado exitosamente con medio de pago: {medio_pago.nombre}",
        "puntos_ganados": puntos_ganados,
        "puntos_usados": puntos_usar,
        "descuento_puntos": descuento_puntos
    }


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
    from sqlalchemy.orm import joinedload
    
    query = db.query(Pedido).options(
        joinedload(Pedido.cliente),
        joinedload(Pedido.items),
        joinedload(Pedido.medio_pago)
    )
    
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
            # Información del medio de pago
            'medio_pago_id': pedido.medio_pago_id,
            'medio_pago_codigo': pedido.medio_pago.codigo if pedido.medio_pago else None,
            'medio_pago_nombre': pedido.medio_pago.nombre if pedido.medio_pago else None,
            'permite_cheque': pedido.medio_pago.permite_cheque if pedido.medio_pago else None,
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
        'local_despacho_id': pedido.local_despacho_id,
        'numero_pedido': f"PED-{pedido.id:05d}",
        'fecha_pedido': pedido.fecha_pedido,
        'total': pedido.monto_total,
        'estado': pedido.estado,
        'pagado': pedido.es_pagado,
        'inventario_descontado': pedido.inventario_descontado,
        'notas': pedido.notas,
        'notas_admin': pedido.notas_admin,
        # Información del medio de pago
        'medio_pago_id': pedido.medio_pago_id,
        'medio_pago_codigo': pedido.medio_pago.codigo if pedido.medio_pago else None,
        'medio_pago_nombre': pedido.medio_pago.nombre if pedido.medio_pago else None,
        'permite_cheque': pedido.medio_pago.permite_cheque if pedido.medio_pago else False,
        # Información de puntos
        'puntos_ganados': pedido.puntos_ganados,
        'puntos_usados': pedido.puntos_usados,
        'descuento_puntos': float(pedido.descuento_puntos) if pedido.descuento_puntos else None,
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
            # Auto-asignar local de despacho si el usuario tiene uno asignado por defecto
            local_despacho_final = pedido_update.local_despacho_id
            if not local_despacho_final and current_user.local_defecto_id:
                local_despacho_final = current_user.local_defecto_id
                pedido.local_despacho_id = local_despacho_final
            
            if not local_despacho_final:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe seleccionar un local de despacho para confirmar el pedido"
                )
            
            # Verificar que haya un turno de caja abierto en el local de despacho
            # EXCEPCIÓN: El local WEB (Tienda Online) no requiere caja abierta
            local_despacho_obj = db.query(Local).filter(Local.id == local_despacho_final).first()
            
            # Solo validar caja abierta para locales físicos (no para tienda online)
            if local_despacho_obj and local_despacho_obj.codigo != 'WEB':
                turno_abierto = db.query(TurnoCaja).filter(
                    and_(
                        TurnoCaja.local_id == local_despacho_final,
                        TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
                    )
                ).first()
                
                if not turno_abierto:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No hay caja abierta en el local de despacho '{local_despacho_obj.nombre}'. Debe abrir un turno de caja antes de confirmar pedidos."
                    )
            
            # Descontar inventario
            descontar_inventario(pedido, local_despacho_final, db)
            
            # Usar puntos si el pedido tenía puntos_usados configurados
            if pedido.puntos_usados and pedido.puntos_usados > 0:
                from decimal import Decimal
                exito, mensaje_puntos, movimiento = PuntosService.usar_puntos_en_pedido(
                    db, 
                    pedido.cliente_id, 
                    pedido.id, 
                    pedido.puntos_usados, 
                    Decimal(str(pedido.descuento_puntos))
                )
                
                if not exito:
                    # Revertir descuento de inventario
                    devolver_inventario(pedido, db)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error al usar puntos: {mensaje_puntos}"
                    )
            
            # Otorgar puntos ganados al cliente si los hay
            if pedido.puntos_ganados and pedido.puntos_ganados > 0:
                PuntosService.otorgar_puntos_por_pedido(
                    db, 
                    pedido.cliente_id, 
                    pedido.id, 
                    pedido.puntos_ganados,
                    f"Puntos ganados por confirmación de pedido #{pedido.id}"
                )
            
            # Registrar venta en caja si hay turno activo del vendedor
            registrar_venta_en_caja(pedido, current_user.id, db)
        
        # Si cambia a CANCELADO
        elif nuevo_estado == "CANCELADO" and estado_anterior != "CANCELADO":
            # Devolver inventario si había sido descontado
            devolver_inventario(pedido, db)
            
            # Devolver puntos ganados si habían sido otorgados y el pedido estaba confirmado
            if estado_anterior == "CONFIRMADO" and pedido.puntos_ganados and pedido.puntos_ganados > 0:
                # Crear movimiento de ajuste para devolver puntos ganados
                from database.models import MovimientoPuntos, TipoMovimientoPuntos
                from datetime import datetime
                
                # Obtener puntos del cliente
                puntos_cliente = PuntosService.obtener_puntos_cliente(db, pedido.cliente_id)
                
                # Crear movimiento de devolución (ajuste negativo)
                movimiento_devolucion = MovimientoPuntos(
                    cliente_id=pedido.cliente_id,
                    pedido_id=pedido.id,
                    tipo_movimiento=TipoMovimientoPuntos.AJUSTE,
                    puntos=-pedido.puntos_ganados,  # Negativo para devolver
                    descripcion=f"Devolución por cancelación de pedido #{pedido.id}",
                    fecha_movimiento=datetime.now()
                )
                db.add(movimiento_devolucion)
                
                # Actualizar puntos del cliente
                puntos_cliente.puntos_disponibles -= pedido.puntos_ganados
                puntos_cliente.puntos_totales_ganados -= pedido.puntos_ganados
                
                # Asegurar que no quede negativo
                if puntos_cliente.puntos_disponibles < 0:
                    puntos_cliente.puntos_disponibles = 0
                if puntos_cliente.puntos_totales_ganados < 0:
                    puntos_cliente.puntos_totales_ganados = 0
            
            # Devolver puntos usados si habían sido usados y el pedido estaba confirmado
            if estado_anterior == "CONFIRMADO" and pedido.puntos_usados and pedido.puntos_usados > 0:
                from database.models import MovimientoPuntos, TipoMovimientoPuntos
                from datetime import datetime
                
                # Obtener puntos del cliente
                puntos_cliente = PuntosService.obtener_puntos_cliente(db, pedido.cliente_id)
                
                # Crear movimiento de ajuste para devolver puntos usados
                movimiento_devolucion_usados = MovimientoPuntos(
                    cliente_id=pedido.cliente_id,
                    pedido_id=pedido.id,
                    tipo_movimiento=TipoMovimientoPuntos.AJUSTE,
                    puntos=pedido.puntos_usados,  # Positivo para devolver
                    descripcion=f"Devolución de puntos usados por cancelación de pedido #{pedido.id}",
                    fecha_movimiento=datetime.now()
                )
                db.add(movimiento_devolucion_usados)
                
                # Actualizar puntos del cliente
                puntos_cliente.puntos_disponibles += pedido.puntos_usados
                puntos_cliente.puntos_totales_usados -= pedido.puntos_usados
                
                # Asegurar que no quede negativo
                if puntos_cliente.puntos_totales_usados < 0:
                    puntos_cliente.puntos_totales_usados = 0
        
        pedido.estado = nuevo_estado
    
    # Si solo se actualiza el local de despacho sin cambiar estado (caso raro pero posible)
    elif pedido_update.local_despacho_id and pedido.estado == "CONFIRMADO" and not pedido.inventario_descontado:
        descontar_inventario(pedido, pedido_update.local_despacho_id, db)
    
    # Actualizar local de despacho si se proporciona explícitamente (no auto-asignado)
    if pedido_update.local_despacho_id:
        pedido.local_despacho_id = pedido_update.local_despacho_id
    
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
        'medio_pago_id': pedido.medio_pago_id,
        'medio_pago_codigo': pedido.medio_pago.codigo if pedido.medio_pago else None,
        'medio_pago_nombre': pedido.medio_pago.nombre if pedido.medio_pago else None,
        'permite_cheque': pedido.medio_pago.permite_cheque if pedido.medio_pago else False,
        'puntos_ganados': pedido.puntos_ganados,
        'puntos_usados': pedido.puntos_usados,
        'descuento_puntos': float(pedido.descuento_puntos) if pedido.descuento_puntos else None,
        'cliente': pedido.cliente,
        'items': pedido.items
    }


@router.get("/{pedido_id}/boleta")
def generar_boleta(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """
    Genera y descarga la boleta en PDF de un pedido.
    
    **Uso:** Backoffice - Generar boleta para impresión o envío
    """
    # Obtener el pedido con todas sus relaciones
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    try:
        # Generar PDF
        pdf_buffer = generar_boleta_pedido(pedido)
        
        # Configurar nombre del archivo
        numero_pedido = f"PED-{pedido.id:05d}"
        nombre_archivo = f"Boleta_{numero_pedido}.pdf"
        
        # Retornar como streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la boleta: {str(e)}"
        )
