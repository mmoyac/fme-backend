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
from database.models import Pedido, ItemPedido, Cliente, Producto, Local, Inventario, MovimientoInventario, TurnoCaja, OperacionCaja, TipoOperacionCaja, EstadoTurnoCaja, TipoPedido, StockCajasProveedor
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
    Descuenta el inventario de los productos del pedido según su tipo.
    
    - PRODUCTOS: Descuenta del inventario regular (tabla Inventario)
    - CAJAS_VARIABLES: Descuenta del stock de cajas proveedor (tabla StockCajasProveedor)
    
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
    
    # Obtener el tipo de pedido
    if not pedido.tipo_pedido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede procesar pedido sin tipo definido"
        )
    
    tipo_codigo = pedido.tipo_pedido.codigo
    
    if tipo_codigo == "PRODUCTOS":
        # Lógica para productos regulares (inventario normal)
        _descontar_inventario_productos(pedido, local_despacho_id, db)
    elif tipo_codigo == "CAJAS_VARIABLES":
        # Lógica para cajas de carne (stock cajas proveedor)
        _descontar_inventario_cajas(pedido, local_despacho_id, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de pedido '{tipo_codigo}' no soportado para descuento de inventario"
        )
    
    # Marcar como descontado (común para ambos tipos)
    pedido.inventario_descontado = True
    pedido.local_despacho_id = local_despacho_id


def _descontar_inventario_productos(pedido: Pedido, local_despacho_id: int, db: Session):
    """Descuenta inventario regular para productos normales."""
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


def _descontar_inventario_cajas(pedido: Pedido, local_despacho_id: int, db: Session):
    """Descuenta stock de cajas proveedor para pedidos de carne usando lotes específicos."""
    from database.models import MovimientoStockCajas, Lote, Enrolamiento, PrecioProveedor
    from decimal import Decimal
    
    nuevo_monto_total = Decimal('0')
    items_actualizados = []
    
    # Obtener lotes específicos para cada item y calcular precio real
    for item in pedido.items:
        # Obtener lotes disponibles para este producto (FIFO - primero en vencer)
        lotes_query = db.query(
            Lote.id,
            Lote.codigo_lote,
            Lote.peso_actual,
            Lote.fecha_vencimiento,
            Lote.lote_proveedor,
            Lote.producto_id,
            PrecioProveedor.precio_kg,
            Enrolamiento.proveedor_id
        ).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).outerjoin(
            PrecioProveedor, and_(
                PrecioProveedor.producto_id == Lote.producto_id,
                PrecioProveedor.proveedor_id == Enrolamiento.proveedor_id,
                PrecioProveedor.activo == True
            )
        ).filter(
            Lote.producto_id == item.producto_id,
            Lote.disponible_venta == True,
            Lote.vendido == False
        ).order_by(
            Lote.fecha_vencimiento.asc()  # FIFO - primero en vencer
        ).limit(item.cantidad)
        
        lotes_disponibles = lotes_query.all()
        
        if len(lotes_disponibles) < item.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay suficientes lotes disponibles de {item.producto.nombre}. Requerido: {item.cantidad}, disponible: {len(lotes_disponibles)}"
            )
        
        # Calcular precio real basado en lotes específicos
        precio_total_item = Decimal('0')
        peso_total_item = Decimal('0')
        
        for lote in lotes_disponibles:
            # Marcar lote como vendido
            lote_obj = db.query(Lote).filter(Lote.id == lote.id).first()
            lote_obj.vendido = True
            lote_obj.disponible_venta = False
            
            # Calcular precio de este lote
            precio_por_kg = Decimal(str(lote.precio_kg)) if lote.precio_kg else Decimal('0')
            peso_lote = Decimal(str(lote.peso_actual))
            precio_lote = peso_lote * precio_por_kg
            
            precio_total_item += precio_lote
            peso_total_item += peso_lote
            
            # Registrar movimiento de lote específico
            movimiento_cajas = MovimientoStockCajas(
                producto_id=item.producto_id,
                proveedor_id=lote.proveedor_id,
                tipo_movimiento="VENTA_LOTE",
                cajas_movimiento=1,  # 1 lote = 1 caja
                peso_total_kg=float(peso_lote),
                descripcion=f"Venta lote {lote.codigo_lote} por pedido #{pedido.id}",
                referencia_tipo="PEDIDO",
                referencia_id=pedido.id,
                lote_codigo=lote.codigo_lote,
                usuario="sistema"
            )
            db.add(movimiento_cajas)
        
        # Actualizar precio unitario del item al precio real
        item.precio_unitario = precio_total_item / item.cantidad
        nuevo_monto_total += precio_total_item
        
        # **AGREGAR: Actualizar stock de cajas por proveedor**
        # Obtener proveedor del primer lote (todos deberían ser del mismo proveedor)
        proveedor_id = lotes_disponibles[0].proveedor_id
        
        # Buscar o crear entrada en stock_cajas_proveedor
        from database.models import StockCajasProveedor
        stock_cajas = db.query(StockCajasProveedor).filter(
            StockCajasProveedor.producto_id == item.producto_id,
            StockCajasProveedor.proveedor_id == proveedor_id
        ).first()
        
        if stock_cajas:
            # Reducir el stock de cajas disponibles
            stock_cajas.cajas_disponibles -= item.cantidad
            stock_cajas.cajas_totales_vendidas += item.cantidad
        
        items_actualizados.append({
            'item_id': item.id,
            'precio_original': float(item.precio_unitario * item.cantidad),
            'precio_real': float(precio_total_item),
            'peso_total': float(peso_total_item),
            'stock_reducido': item.cantidad,
            'proveedor_id': proveedor_id
        })
    
    # Actualizar monto total del pedido con precio real
    monto_original = pedido.monto_total
    pedido.monto_total = nuevo_monto_total
    
    # Log para auditoría
    print(f"Pedido #{pedido.id}: Precio actualizado de ${monto_original} a ${nuevo_monto_total}")
    print(f"Items actualizados: {items_actualizados}")


def devolver_inventario(pedido: Pedido, db: Session):
    """
    Devuelve el inventario al cancelar un pedido según su tipo.
    
    - PRODUCTOS: Devuelve al inventario regular (tabla Inventario)
    - CAJAS_VARIABLES: Devuelve al stock de cajas proveedor (tabla StockCajasProveedor)
    
    Args:
        pedido: El pedido del cual devolver inventario
        db: Sesión de base de datos
    """
    if not pedido.inventario_descontado or not pedido.local_despacho_id:
        return  # No hay nada que devolver
    
    # Obtener el tipo de pedido
    if not pedido.tipo_pedido:
        return  # No se puede procesar sin tipo
    
    tipo_codigo = pedido.tipo_pedido.codigo
    
    if tipo_codigo == "PRODUCTOS":
        # Lógica para productos regulares
        _devolver_inventario_productos(pedido, db)
    elif tipo_codigo == "CAJAS_VARIABLES":
        # Lógica para cajas de carne
        _devolver_inventario_cajas(pedido, db)
    
    # Marcar como no descontado (común para ambos tipos)
    pedido.inventario_descontado = False


def _devolver_inventario_productos(pedido: Pedido, db: Session):
    """Devuelve inventario regular para productos normales."""
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


def _devolver_inventario_cajas(pedido: Pedido, db: Session):
    """Devuelve lotes específicos de cajas al estado original para pedidos de carne."""
    from database.models import MovimientoStockCajas, Lote
    
    # Buscar movimientos de venta de lotes específicos para este pedido
    movimientos_venta = db.query(MovimientoStockCajas).filter(
        MovimientoStockCajas.referencia_tipo == "PEDIDO",
        MovimientoStockCajas.referencia_id == pedido.id,
        MovimientoStockCajas.tipo_movimiento == "VENTA_LOTE"
    ).all()
    
    if not movimientos_venta:
        # Fallback al método anterior si no hay movimientos de lote específico
        for item in pedido.items:
            # Buscar el stock de cajas para devolver
            stock_cajas = db.query(StockCajasProveedor).filter(
                StockCajasProveedor.producto_id == item.producto_id
            ).order_by(StockCajasProveedor.id.desc()).first()  # El más reciente
            
            if stock_cajas:
                # Devolver cajas al stock
                stock_cajas.cajas_disponibles += item.cantidad
                stock_cajas.cajas_vendidas -= item.cantidad
                
                # Registrar movimiento de devolución de cajas
                movimiento_cajas = MovimientoStockCajas(
                    stock_cajas_id=stock_cajas.id,
                    tipo_movimiento="DEVOLUCION",
                    cajas_movimiento=item.cantidad,
                    peso_total_kg=item.cantidad * stock_cajas.peso_promedio_caja_kg,
                    referencia_tipo="PEDIDO",
                    referencia_id=pedido.id,
                    notas=f"Devolución de {item.cantidad} cajas por cancelación de pedido #{pedido.id}",
                    usuario="sistema"
                )
                db.add(movimiento_cajas)
        return
    
    # Devolver lotes específicos a su estado original
    for movimiento in movimientos_venta:
        if movimiento.lote_codigo:
            # Buscar el lote específico
            lote = db.query(Lote).filter(
                Lote.codigo_lote == movimiento.lote_codigo
            ).first()
            
            if lote:
                # Restaurar lote al estado disponible
                lote.vendido = False
                lote.disponible_venta = True
                
                # **AGREGAR: Restaurar stock de cajas por proveedor**
                from database.models import StockCajasProveedor
                stock_cajas = db.query(StockCajasProveedor).filter(
                    StockCajasProveedor.producto_id == movimiento.producto_id,
                    StockCajasProveedor.proveedor_id == movimiento.proveedor_id
                ).first()
                
                if stock_cajas:
                    # Aumentar el stock de cajas disponibles
                    stock_cajas.cajas_disponibles += 1
                    # Solo decrementar si hay ventas registradas (evitar negativos)
                    if stock_cajas.cajas_totales_vendidas > 0:
                        stock_cajas.cajas_totales_vendidas -= 1
                
                # Registrar movimiento de devolución del lote
                movimiento_devolucion = MovimientoStockCajas(
                    producto_id=movimiento.producto_id,
                    proveedor_id=movimiento.proveedor_id,
                    tipo_movimiento="DEVOLUCION_LOTE",
                    cajas_movimiento=1,  # 1 lote = 1 caja
                    peso_total_kg=movimiento.peso_total_kg,
                    descripcion=f"Devolución lote {movimiento.lote_codigo} por cancelación de pedido #{pedido.id}",
                    referencia_tipo="PEDIDO",
                    referencia_id=pedido.id,
                    lote_codigo=movimiento.lote_codigo,
                    usuario="sistema"
                )
                db.add(movimiento_devolucion)
                
                print(f"Lote {movimiento.lote_codigo} devuelto al estado disponible y stock incrementado")


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
        joinedload(Pedido.medio_pago),
        joinedload(Pedido.tipo_pedido),
        joinedload(Pedido.tipo_documento_tributario)
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
            # Información de tipo de pedido
            'tipo_pedido_id': pedido.tipo_pedido_id,
            'tipo_pedido_codigo': pedido.tipo_pedido.codigo if pedido.tipo_pedido else None,
            'tipo_pedido_nombre': pedido.tipo_pedido.nombre if pedido.tipo_pedido else None,
            # Control SII (Facturación Electrónica)  
            'tipo_documento_tributario_id': pedido.tipo_documento_tributario_id,
            'tipo_documento_codigo': pedido.tipo_documento_tributario.codigo if pedido.tipo_documento_tributario else None,
            'tipo_documento_nombre': pedido.tipo_documento_tributario.nombre if pedido.tipo_documento_tributario else None,
            'estado_sii': pedido.estado_sii,
            'folio_sii': pedido.folio_sii,
            'numero_dte': pedido.numero_dte,
            'fecha_envio_sii': pedido.fecha_envio_sii,
            'fecha_respuesta_sii': pedido.fecha_respuesta_sii,
            'observaciones_sii': pedido.observaciones_sii,
            # Información de puntos
            'puntos_ganados': pedido.puntos_ganados,
            'puntos_usados': pedido.puntos_usados,
            'descuento_puntos': float(pedido.descuento_puntos) if pedido.descuento_puntos else None,
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
        'tipo_pedido_id': pedido.tipo_pedido_id,
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
        # Información de tipo de pedido
        'tipo_pedido_codigo': pedido.tipo_pedido.codigo if pedido.tipo_pedido else None,
        'tipo_pedido_nombre': pedido.tipo_pedido.nombre if pedido.tipo_pedido else None,
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
            # Auto-asignar local de despacho basado en el tipo de pedido
            local_despacho_final = pedido_update.local_despacho_id
            
            if not local_despacho_final:
                # 1. Intentar usar el local default del tipo de pedido
                if pedido.tipo_pedido and pedido.tipo_pedido.local_despacho_default_id:
                    local_despacho_final = pedido.tipo_pedido.local_despacho_default_id
                    pedido.local_despacho_id = local_despacho_final
                # 2. Si no hay default del tipo, usar local default del usuario
                elif current_user.local_defecto_id:
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
        'tipo_pedido_id': pedido.tipo_pedido_id,
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
        # Información de tipo de pedido
        'tipo_pedido_codigo': pedido.tipo_pedido.codigo if pedido.tipo_pedido else None,
        'tipo_pedido_nombre': pedido.tipo_pedido.nombre if pedido.tipo_pedido else None,
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


@router.put("/{pedido_id}/estado-sii")
def actualizar_estado_sii(
    pedido_id: int,
    estado_sii: str,
    observaciones: str = "",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza el estado SII de una factura.
    
    Estados válidos: PENDIENTE, ENVIADO, APROBADO, RECHAZADO
    """
    # Validar estados permitidos
    estados_validos = ["PENDIENTE", "ENVIADO", "APROBADO", "RECHAZADO"]
    if estado_sii not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado SII inválido. Estados válidos: {', '.join(estados_validos)}"
        )
    
    # Buscar el pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    # Verificar que sea una factura
    if pedido.tipo_documento_tributario_id != 1:  # 1 = FAC
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede actualizar el estado SII de facturas"
        )
    
    # Actualizar estado
    pedido.estado_sii = estado_sii
    if estado_sii == "ENVIADO" and not pedido.fecha_envio_sii:
        from datetime import datetime
        pedido.fecha_envio_sii = datetime.now()
    elif estado_sii in ["APROBADO", "RECHAZADO"] and not pedido.fecha_respuesta_sii:
        from datetime import datetime
        pedido.fecha_respuesta_sii = datetime.now()
    
    if observaciones:
        pedido.observaciones_sii = observaciones
    
    db.commit()
    db.refresh(pedido)
    
    return {
        "pedido_id": pedido_id,
        "estado_sii": estado_sii,
        "fecha_envio_sii": pedido.fecha_envio_sii,
        "fecha_respuesta_sii": pedido.fecha_respuesta_sii,
        "mensaje": f"Estado SII actualizado a {estado_sii}"
    }
