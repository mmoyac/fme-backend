"""
Router para endpoints de Pedidos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import io
from decimal import Decimal

from database.database import get_db
from database.models import Pedido, ItemPedido, Cliente, Producto, Local, Inventario, MovimientoInventario, TurnoCaja, OperacionCaja, TipoOperacionCaja, EstadoTurnoCaja, TipoPedido, StockCajasProveedor, MedioPago, CobroPendiente
from schemas.pedido import (
    PedidoCreateFrontend,
    PedidoCreateBackoffice,
    PedidoConfirmacion,
    PedidoResponse,
    PedidoConRelaciones,
    PedidoUpdate,
    EstadoPedido
)

from routers.auth import get_current_active_user, get_current_user_or_api_key, ApiKeyUser
from services.boleta_service import generar_boleta_pedido
from services.credito_service import CreditoService
from services.puntos_service import PuntosService
from services.comisiones_service import generar_comision
from services.tenant_service import obtener_siguiente_numero_pedido, get_tenant_from_request

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
    
    # 🔍 DETECTAR SI LOS LOTES YA FUERON RESERVADOS AL CREAR EL PEDIDO
    # Buscar si hay lotes con disponible_venta=False y vendido=False para este pedido
    # (esto indica que fueron reservados en la creación)
    lotes_reservados_count = db.query(Lote).join(
        MovimientoStockCajas, Lote.codigo_lote == MovimientoStockCajas.lote_codigo
    ).filter(
        MovimientoStockCajas.referencia_tipo == "PEDIDO",
        MovimientoStockCajas.referencia_id == pedido.id,
        MovimientoStockCajas.tipo_movimiento == "RESERVA_LOTE",
        Lote.disponible_venta == False,
        Lote.vendido == False
    ).count()
    
    lotes_ya_asignados = lotes_reservados_count > 0
    
    if lotes_ya_asignados:
        print(f"✅ Pedido #{pedido.id}: Lotes ya asignados. Solo marcando como vendidos...")
    
    # Obtener lotes específicos para cada item y calcular precio real
    for item in pedido.items:
        # Si los lotes ya están asignados, buscarlos por los movimientos de reserva
        if lotes_ya_asignados:
            # Buscar lotes reservados para este pedido y producto
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
            ).join(
                MovimientoStockCajas, Lote.codigo_lote == MovimientoStockCajas.lote_codigo
            ).filter(
                Lote.producto_id == item.producto_id,
                MovimientoStockCajas.referencia_tipo == "PEDIDO",
                MovimientoStockCajas.referencia_id == pedido.id,
                MovimientoStockCajas.tipo_movimiento == "RESERVA_LOTE",
                Lote.disponible_venta == False,
                Lote.vendido == False
            ).order_by(
                Lote.fecha_vencimiento.asc()
            ).limit(item.cantidad)
        else:
            # Flujo original: buscar lotes disponibles (FIFO)
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
        lote_id_principal = None  # Para asignar al item (primer lote)
        
        for idx, lote in enumerate(lotes_disponibles):
            # Marcar lote como vendido
            lote_obj = db.query(Lote).filter(Lote.id == lote.id).first()
            lote_obj.vendido = True
            lote_obj.disponible_venta = False
            
            # Guardar el primer lote como lote_id del item
            if idx == 0:
                lote_id_principal = lote.id
            
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
        
        # ✅ ASIGNAR LOTE_ID AL ITEM (para trazabilidad y despacho)
        if lote_id_principal:
            item.lote_id = lote_id_principal
        
        # Aplicar IVA si el precio del producto no lo incluye (precio_kg es neto sin IVA)
        from database.models import Producto as ProductoModel
        producto_obj = db.query(ProductoModel).filter(ProductoModel.id == item.producto_id).first()
        print(f"🔍 [Confirmación] Producto {item.producto_id}: precio_incluye_iva={producto_obj.precio_incluye_iva if producto_obj else 'NO ENCONTRADO'}")
        if producto_obj and not producto_obj.precio_incluye_iva:
            IVA_RATE = Decimal('0.19')
            precio_total_item = precio_total_item * (1 + IVA_RATE)
            print(f"✅ [Confirmación] IVA aplicado: neto={float(precio_total_item / Decimal('1.19')):.0f} → total={float(precio_total_item):.0f}")
        
        # Actualizar precio unitario al precio real (con IVA si aplica)
        item.precio_unitario_venta = float(precio_total_item / Decimal(str(item.cantidad)))
        
        nuevo_monto_total += precio_total_item
        
        # **Actualizar stock de cajas por proveedor**
        # IMPORTANTE: Solo actualizar stock si los lotes NO estaban previamente asignados
        # Si ya estaban reservados, el stock ya fue descontado al crear el pedido
        proveedor_id = lotes_disponibles[0].proveedor_id
        
        from database.models import StockCajasProveedor
        stock_cajas = db.query(StockCajasProveedor).filter(
            StockCajasProveedor.producto_id == item.producto_id,
            StockCajasProveedor.proveedor_id == proveedor_id
        ).first()
        
        if stock_cajas:
            if not lotes_ya_asignados:
                # Solo descontar stock si NO estaba previamente asignado
                stock_cajas.cajas_disponibles -= item.cantidad
                print(f"📦 Stock descontado: {stock_cajas.cajas_disponibles} cajas disponibles")
            
            # Siempre incrementar cajas_totales_vendidas al confirmar
            stock_cajas.cajas_totales_vendidas += item.cantidad
            print(f"✅ Cajas vendidas: {stock_cajas.cajas_totales_vendidas} total")
        
        items_actualizados.append({
            'item_id': item.id,
            'precio_original': float(item.precio_unitario_venta * item.cantidad),
            'precio_real': float(precio_total_item),
            'peso_total': float(peso_total_item),
            'stock_reducido': item.cantidad,
            'proveedor_id': proveedor_id
        })
    
    # Actualizar monto total del pedido con precio real (con IVA si el producto no lo incluye)
    monto_original = pedido.monto_total
    pedido.monto_total = nuevo_monto_total
    print(f"Pedido #{pedido.id}: Precio actualizado de ${monto_original} a ${nuevo_monto_total}")
    
    # Log para auditoría
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
    # Obtener el tipo de pedido
    if not pedido.tipo_pedido:
        return  # No se puede procesar sin tipo
    
    tipo_codigo = pedido.tipo_pedido.codigo
    
    # Para PRODUCTOS: validar que haya inventario descontado y local de despacho
    if tipo_codigo == "PRODUCTOS":
        if not pedido.inventario_descontado or not pedido.local_despacho_id:
            return  # No hay nada que devolver
        _devolver_inventario_productos(pedido, db)
    
    # Para CAJAS_VARIABLES: no requiere validación de inventario_descontado ni local_despacho_id
    # porque los lotes se reservan inmediatamente al crear el pedido (estado PENDIENTE)
    elif tipo_codigo == "CAJAS_VARIABLES":
        _devolver_inventario_cajas(pedido, db)
    
    # Marcar como no descontado (solo para productos que requieren descuento)
    if pedido.inventario_descontado:
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
    from database.models import MovimientoStockCajas, Lote, StockCajasProveedor
    
    # Buscar movimientos de lotes para este pedido (tanto RESERVA como VENTA)
    movimientos_lotes = db.query(MovimientoStockCajas).filter(
        MovimientoStockCajas.referencia_tipo == "PEDIDO",
        MovimientoStockCajas.referencia_id == pedido.id,
        MovimientoStockCajas.tipo_movimiento.in_(["VENTA_LOTE", "RESERVA_LOTE"])
    ).all()
    
    if not movimientos_lotes:
        # Fallback: no hay movimientos de lote registrados, restaurar stock directamente
        for item in pedido.items:
            stock_cajas = db.query(StockCajasProveedor).filter(
                StockCajasProveedor.producto_id == item.producto_id
            ).order_by(StockCajasProveedor.id.desc()).first()
            
            if stock_cajas:
                stock_cajas.cajas_disponibles += item.cantidad
                if stock_cajas.cajas_totales_vendidas >= item.cantidad:
                    stock_cajas.cajas_totales_vendidas -= item.cantidad
                
                movimiento_cajas = MovimientoStockCajas(
                    producto_id=item.producto_id,
                    proveedor_id=stock_cajas.proveedor_id,
                    tipo_movimiento="DEVOLUCION_LOTE",
                    cajas_movimiento=item.cantidad,
                    peso_total_kg=float(item.cantidad * (stock_cajas.peso_promedio_caja_kg or 0)),
                    descripcion=f"Devolución de {item.cantidad} cajas por cancelación de pedido #{pedido.id}",
                    referencia_tipo="PEDIDO",
                    referencia_id=pedido.id,
                    usuario="sistema"
                )
                db.add(movimiento_cajas)
            
            # Restaurar lotes reservados (flujo preventa: lote.reservado=True sin movimientos)
            lotes_a_liberar = db.query(Lote).filter(
                Lote.producto_id == item.producto_id,
                Lote.reservado == True,
                Lote.vendido == False,
            ).limit(int(item.cantidad)).all()
            for lote_r in lotes_a_liberar:
                lote_r.reservado = False
                print(f"🔓 Lote {lote_r.codigo_lote} liberado (reservado→False) por cancelación pedido #{pedido.id}")
        return
    
    # Deduplicar por lote_codigo: si hay RESERVA_LOTE y VENTA_LOTE para el mismo lote,
    # quedarnos solo con VENTA_LOTE (mayor prioridad). Así cada lote se procesa UNA sola vez.
    movimientos_por_lote: dict[str, MovimientoStockCajas] = {}
    for mov in movimientos_lotes:
        if not mov.lote_codigo:
            continue
        previo = movimientos_por_lote.get(mov.lote_codigo)
        if previo is None or mov.tipo_movimiento == "VENTA_LOTE":
            movimientos_por_lote[mov.lote_codigo] = mov

    # Devolver lotes específicos a su estado original (una vez por lote)
    for movimiento in movimientos_por_lote.values():
        if movimiento.lote_codigo:
            # Buscar el lote específico
            lote = db.query(Lote).filter(
                Lote.codigo_lote == movimiento.lote_codigo
            ).first()
            
            if lote:
                # Restaurar lote al estado disponible
                lote.vendido = False
                lote.disponible_venta = True
                
                # **Restaurar stock de cajas (tanto VENTA como RESERVA)**
                es_venta = movimiento.tipo_movimiento == "VENTA_LOTE"
                es_reserva = movimiento.tipo_movimiento == "RESERVA_LOTE"
                
                if es_venta or es_reserva:
                    from database.models import StockCajasProveedor
                    stock_cajas = db.query(StockCajasProveedor).filter(
                        StockCajasProveedor.producto_id == movimiento.producto_id,
                        StockCajasProveedor.proveedor_id == movimiento.proveedor_id
                    ).first()
                    
                    if stock_cajas:
                        # Aumentar el stock de cajas disponibles (común para ambos)
                        stock_cajas.cajas_disponibles += 1
                        
                        # Solo si era venta, decrementar cajas_totales_vendidas
                        if es_venta and stock_cajas.cajas_totales_vendidas > 0:
                            stock_cajas.cajas_totales_vendidas -= 1
                        
                        print(f"📦 Stock restaurado: {stock_cajas.cajas_disponibles} cajas disponibles")
                
                # Eliminar AsignacionPicking del lote (evita registros huérfanos)
                from database.models import AsignacionPicking as AsignacionPickingModel
                asignaciones_huerfanas = db.query(AsignacionPickingModel).filter(
                    AsignacionPickingModel.lote_id == lote.id
                ).all()
                for asig in asignaciones_huerfanas:
                    db.delete(asig)
                    print(f"🗑️ AsignacionPicking ID={asig.id} eliminada (lote {lote.codigo_lote}, pedido cancelado #{pedido.id})")

                # Registrar movimiento de devolución del lote
                tipo_devolucion = "DEVOLUCION_LOTE" if es_venta else "LIBERACION_RESERVA"
                movimiento_devolucion = MovimientoStockCajas(
                    producto_id=movimiento.producto_id,
                    proveedor_id=movimiento.proveedor_id,
                    tipo_movimiento=tipo_devolucion,
                    cajas_movimiento=1,  # 1 lote = 1 caja
                    peso_total_kg=movimiento.peso_total_kg,
                    descripcion=f"{'Devolución' if es_venta else 'Liberación'} lote {movimiento.lote_codigo} por cancelación de pedido #{pedido.id}",
                    referencia_tipo="PEDIDO",
                    referencia_id=pedido.id,
                    lote_codigo=movimiento.lote_codigo,
                    usuario="sistema"
                )
                db.add(movimiento_devolucion)
                
                print(f"Lote {movimiento.lote_codigo} devuelto al estado disponible y stock restaurado")


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
def crear_pedido_frontend(
    request: Request,
    pedido_data: PedidoCreateFrontend, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo pedido desde el frontend (sin autenticación).
    
    **Flujo:**
    1. Detecta el tenant desde el dominio de la petición
    2. Busca o crea el cliente con el email (en el tenant correspondiente)
    3. Valida que los productos existan y tengan precio en local WEB del tenant
    4. Crea el pedido con estado PENDIENTE
    5. Crea los items del pedido
    6. Calcula el monto total
    
    **Uso:** Landing - Checkout del carrito
    """
    # 0. Detectar tenant desde el dominio
    tenant = get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo detectar el tenant desde el dominio"
        )
    
    tenant_id = tenant.id
    print(f"🎯 Pedido frontend - Tenant detectado: {tenant.nombre} (ID: {tenant_id})")
    
    # 1. Buscar local WEB del tenant
    local_web = db.query(Local).filter(
        Local.codigo == 'WEB',
        Local.tenant_id == tenant_id
    ).first()
    
    if not local_web:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Local WEB no configurado para {tenant.nombre}"
        )

    # 1.5. Buscar medio de pago por código (dato maestro global)
    from database.models import MedioPago
    medio_pago = None
    if pedido_data.medio_pago_codigo:
        medio_pago = db.query(MedioPago).filter(
            MedioPago.codigo == pedido_data.medio_pago_codigo
        ).first()
        if not medio_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medio de pago '{pedido_data.medio_pago_codigo}' no encontrado"
            )
    
    # 2. Buscar o crear cliente (en el tenant correspondiente)
    cliente = db.query(Cliente).filter(
        Cliente.email == pedido_data.cliente_email,
        Cliente.tenant_id == tenant_id
    ).first()
    
    if not cliente:
        # Crear nuevo cliente en el tenant detectado
        cliente = Cliente(
            tenant_id=tenant_id,
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
    
    # 3. Validar productos y calcular total (en el tenant correspondiente)
    items_a_crear = []
    monto_total = 0.0
    
    for item_data in pedido_data.items:
        # Buscar producto por SKU en el tenant
        producto = db.query(Producto).filter(
            Producto.sku == item_data.sku,
            Producto.tenant_id == tenant_id
        ).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con SKU {item_data.sku} no encontrado"
            )
        
        # Obtener precio del producto para el local WEB del tenant
        from database.models import Precio
        precio = db.query(Precio).filter(
            Precio.producto_id == producto.id,
            Precio.local_id == local_web.id
        ).first()
        
        if not precio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto {producto.nombre} no tiene precio configurado en {tenant.nombre}"
            )
        
        # Preparar item
        items_a_crear.append({
            'producto_id': producto.id,
            'cantidad': item_data.cantidad,
            'precio_unitario_venta': precio.monto_precio
        })
        
        # Redondear subtotal individual para evitar centavos
        subtotal = round(precio.monto_precio * item_data.cantidad)
        monto_total += subtotal
    
    # El total ya está redondeado gracias a la suma de subtotales redondeados
    
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
    
    # 4. Generar numero_pedido único para el tenant
    numero_pedido = obtener_siguiente_numero_pedido(db, tenant_id)
    
    # 4.5. Obtener estado PENDIENTE
    from database.models import EstadoPedido as EstadoPedidoModel
    estado_pendiente = db.query(EstadoPedidoModel).filter(EstadoPedidoModel.codigo == 'PENDIENTE').first()
    if not estado_pendiente:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Estado PENDIENTE no configurado en el sistema"
        )
    
    # 5. Crear pedido
    db_pedido = Pedido(
        tenant_id=tenant_id,
        numero_pedido=numero_pedido,
        cliente_id=cliente.id,
        local_id=local_web.id,
        medio_pago_id=medio_pago.id if medio_pago else None,
        monto_total=monto_total,
        estado_id=estado_pendiente.id,
        es_pagado=False,
        notas=pedido_data.notas,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos,
        canal_venta_id=2  # LANDING — pedidos desde la tienda online
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
        numero_pedido=db_pedido.numero_pedido,
        monto_total=monto_total,
        estado=db_pedido.estado_pedido.codigo if db_pedido.estado_pedido else 'PENDIENTE',
        mensaje="¡Pedido recibido! Te contactaremos pronto para coordinar el pago y entrega.",
        puntos_ganados=puntos_ganados,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos
    )


@router.post("/backoffice", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_pedido_backoffice(
    pedido_data: PedidoCreateBackoffice,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_api_key)
):
    """
    Crea un nuevo pedido desde el backoffice.
    
    **Flujo:**
    1. Valida que el cliente, local y medio de pago existan y pertenezcan al tenant
    2. Valida que todos los productos existan y pertenezcan al tenant
    3. Crea el pedido con estado PENDIENTE
    4. Crea los items del pedido con los precios especificados
    5. Calcula el monto total
    
    **Uso:** Backoffice - Crear pedido manual / Integraciones externas (n8n via X-API-Key)
    """
    # Resolver tenant_id: desde el usuario JWT o desde el body (cuando es API Key)
    if isinstance(current_user, ApiKeyUser):
        if not pedido_data.canal_venta_id or not getattr(pedido_data, 'tenant_id', None):
            # Para API Key, el tenant_id debe venir en el body — usamos el del cliente
            pass  # Se resolverá por el cliente_id más abajo
        tenant_id_efectivo = getattr(pedido_data, 'tenant_id', None)
        if not tenant_id_efectivo:
            raise HTTPException(status_code=400, detail="Se requiere tenant_id en el body cuando se usa X-API-Key")
    else:
        tenant_id_efectivo = current_user.tenant_id

    # 1. Validar que el cliente exista y pertenezca al tenant
    cliente = db.query(Cliente).filter(Cliente.id == pedido_data.cliente_id, Cliente.tenant_id == tenant_id_efectivo).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {pedido_data.cliente_id} no encontrado"
        )
    
    # 2. Validar que el local exista y pertenezca al tenant
    local = db.query(Local).filter(Local.id == pedido_data.local_id, Local.tenant_id == tenant_id_efectivo).first()
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
            'precio_unitario_venta': item_data.precio_unitario_venta,
            'local_cliente_id': item_data.local_cliente_id
        })

        # Redondear subtotal individual para evitar centavos
        subtotal = round(item_data.precio_unitario_venta * item_data.cantidad)
        monto_total += subtotal

    # 4.2.5. Si requiere delivery, validar que todos los productos tienen peso_bruto configurado
    requiere_delivery_check = getattr(pedido_data, 'requiere_delivery', False)
    if requiere_delivery_check:
        productos_sin_peso = []
        for item_data in pedido_data.items:
            prod = db.query(Producto).filter(Producto.id == item_data.producto_id).first()
            if prod and (prod.peso_bruto is None or prod.peso_bruto <= 0):
                productos_sin_peso.append(f"{prod.sku} - {prod.nombre}")
        if productos_sin_peso:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Los siguientes productos no tienen peso bruto configurado y no pueden incluirse en un pedido con delivery: {', '.join(productos_sin_peso)}"
            )

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
    
    # 4.5. Validar crédito si el medio de pago es diferido (cheque o plazo_dias > 0)
    es_pago_diferido = medio_pago.permite_cheque or (medio_pago.plazo_dias or 0) > 0
    if es_pago_diferido:
        es_valido, mensaje = CreditoService.validar_credito_disponible(
            cliente.id, monto_total, db
        )
        if not es_valido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje
            )
    
    # 5. Generar numero_pedido único para el tenant
    numero_pedido = obtener_siguiente_numero_pedido(db, tenant_id_efectivo)

    # 5.5. Obtener estado PENDIENTE
    from database.models import EstadoPedido as EstadoPedidoModel
    estado_pendiente = db.query(EstadoPedidoModel).filter(EstadoPedidoModel.codigo == 'PENDIENTE').first()
    if not estado_pendiente:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Estado PENDIENTE no configurado en el sistema"
        )

    # 6. Crear pedido
    db_pedido = Pedido(
        tenant_id=tenant_id_efectivo,
        numero_pedido=numero_pedido,
        cliente_id=cliente.id,
        local_id=local.id,
        medio_pago_id=medio_pago.id,
        tipo_pedido_id=pedido_data.tipo_pedido_id,
        tipo_documento_tributario_id=pedido_data.tipo_documento_tributario_id,
        usuario_id=current_user.id if not isinstance(current_user, ApiKeyUser) else None,
        monto_total=monto_total,
        estado_id=estado_pendiente.id,
        es_pagado=False,
        notas=pedido_data.notas,
        puntos_usados=puntos_usar,
        descuento_puntos=descuento_puntos,
        canal_venta_id=getattr(pedido_data, 'canal_venta_id', None),
        costo_delivery=getattr(pedido_data, 'costo_delivery', None)
    )
    db.add(db_pedido)
    db.flush()  # Para obtener el ID
    
    # 7. Crear items del pedido PRIMERO
    for item_info in items_a_crear:
        item = ItemPedido(
            pedido_id=db_pedido.id,
            **item_info
        )
        db.add(item)
    
    # 7.5. Hacer flush y refresh para cargar relaciones
    db.flush()
    db.refresh(db_pedido)
    
    # 7.6. DESPUÉS calcular puntos que se ganarían (ahora que los items existen)
    puntos_ganados = PuntosService.calcular_puntos_por_pedido(db, db_pedido.id)
    db_pedido.puntos_ganados = puntos_ganados
    
    # 🥩 LÓGICA DE ASIGNACIÓN INMEDIATA PARA CAJAS VARIABLES
    # Para pedidos tipo CAJAS_VARIABLES, asignamos lotes específicos inmediatamente
    # (no esperamos a confirmación) para bloquear inventario y calcular precio real
    if pedido_data.tipo_pedido_id == 2:  # CAJAS_VARIABLES
        from database.models import MovimientoStockCajas, Lote, Enrolamiento, PrecioProveedor
        from decimal import Decimal
        
        nuevo_monto_total = Decimal('0')
        
        # Asignar lotes para cada item del pedido
        for item in db_pedido.items:
            # Buscar lotes disponibles (FIFO por fecha de vencimiento)
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
            
            # Validar que hay suficientes lotes
            if len(lotes_disponibles) < item.cantidad:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No hay suficientes lotes disponibles de {item.producto.nombre}. Requerido: {item.cantidad}, disponible: {len(lotes_disponibles)}"
                )
            
            # Calcular precio real basado en peso de lotes específicos
            precio_total_item = Decimal('0')
            peso_total_item = Decimal('0')
            
            for lote in lotes_disponibles:
                # Marcar lote como NO disponible para venta (reservado)
                lote_obj = db.query(Lote).filter(Lote.id == lote.id).first()
                lote_obj.disponible_venta = False  # Bloquear para otros pedidos
                # NOTA: vendido=False todavía (se marca True al confirmar)
                
                # Calcular precio de este lote específico
                precio_por_kg = Decimal(str(lote.precio_kg)) if lote.precio_kg else Decimal('0')
                peso_lote = Decimal(str(lote.peso_actual))
                precio_lote = peso_lote * precio_por_kg
                
                precio_total_item += precio_lote
                peso_total_item += peso_lote
                
                # Registrar movimiento informativo (no afecta stock aún)
                movimiento_cajas = MovimientoStockCajas(
                    producto_id=item.producto_id,
                    proveedor_id=lote.proveedor_id,
                    tipo_movimiento="RESERVA_LOTE",
                    cajas_movimiento=1,
                    peso_total_kg=float(peso_lote),
                    descripcion=f"Reserva lote {lote.codigo_lote} para pedido #{db_pedido.id}",
                    referencia_tipo="PEDIDO",
                    referencia_id=db_pedido.id,
                    lote_codigo=lote.codigo_lote,
                    usuario=current_user.email
                )
                db.add(movimiento_cajas)
            
            # **ACTUALIZAR: Reducir stock de cajas disponibles**
            # Obtener proveedor del primer lote (todos deberían ser del mismo)
            proveedor_id = lotes_disponibles[0].proveedor_id
            
            from database.models import StockCajasProveedor
            stock_cajas = db.query(StockCajasProveedor).filter(
                StockCajasProveedor.producto_id == item.producto_id,
                StockCajasProveedor.proveedor_id == proveedor_id
            ).first()
            
            if stock_cajas:
                # Reducir el stock de cajas disponibles (reservadas)
                stock_cajas.cajas_disponibles -= item.cantidad
                print(f"📦 Stock actualizado: {stock_cajas.cajas_disponibles} cajas disponibles de {item.producto.nombre}")
            
            # Aplicar IVA si el precio del producto no lo incluye (precio_kg es neto sin IVA)
            from database.models import Producto as ProductoModel
            producto_obj = db.query(ProductoModel).filter(ProductoModel.id == item.producto_id).first()
            print(f"🔍 Producto {item.producto_id}: precio_incluye_iva={producto_obj.precio_incluye_iva if producto_obj else 'NO ENCONTRADO'}")
            if producto_obj and not producto_obj.precio_incluye_iva:
                IVA_RATE = Decimal('0.19')
                precio_total_item = precio_total_item * (1 + IVA_RATE)
                print(f"✅ IVA aplicado: neto={float(precio_total_item / Decimal('1.19')):.0f} → total={float(precio_total_item):.0f}")
            
            # Actualizar precio unitario del item con precio real (con IVA si aplica)
            item.precio_unitario_venta = float(precio_total_item / Decimal(str(item.cantidad)))
            nuevo_monto_total += precio_total_item
        
        # Actualizar monto total del pedido con precio real (con IVA si el producto no lo incluye)
        monto_total = nuevo_monto_total  # Variable local para retorno
        db_pedido.monto_total = nuevo_monto_total
        
        print(f"✅ Pedido CAJAS_VARIABLES #{db_pedido.id}: Lotes asignados. Precio real: ${nuevo_monto_total}")
    
    # 🏪 LÓGICA DE AUTO-CONFIRMACIÓN PARA PEDIDOS DE TIENDA (POS)
    # Si el pedido es de un local físico (no WEB) y no es CAJAS_VARIABLES,
    # se confirma y entrega automáticamente (flujo directo de venta en mostrador)
    
    # Verificar tipo de pedido (ahora la relación está cargada)
    tipo_codigo = db_pedido.tipo_pedido.codigo if db_pedido.tipo_pedido else None
    
    es_pedido_pos_directo = (
        local.codigo != 'WEB' and 
        tipo_codigo == 'PRODUCTOS'  # Solo productos regulares, no cajas variables
    )
    
    # Si el vendedor marcó delivery, el pedido queda solo CONFIRMADO (no ENTREGADO)
    requiere_delivery = getattr(pedido_data, 'requiere_delivery', False)
    
    estado_final_id = estado_pendiente.id
    mensaje_final = f"Pedido creado exitosamente con medio de pago: {medio_pago.nombre}"
    
    if es_pedido_pos_directo:
        # 🎯 PEDIDO POS: Confirmar y entregar automáticamente
        estado_confirmado = db.query(EstadoPedidoModel).filter(EstadoPedidoModel.codigo == 'CONFIRMADO').first()
        estado_entregado = db.query(EstadoPedidoModel).filter(EstadoPedidoModel.codigo == 'ENTREGADO').first()
        
        if not estado_confirmado or not estado_entregado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estados CONFIRMADO/ENTREGADO no configurados"
            )
        
        # Asignar local de despacho (mismo local donde se creó)
        db_pedido.local_despacho_id = local.id
        
        # Validar que haya caja abierta
        turno_abierto = db.query(TurnoCaja).filter(
            and_(
                TurnoCaja.local_id == local.id,
                TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
            )
        ).first()
        
        if not turno_abierto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay caja abierta en el local '{local.nombre}'. Debe abrir un turno de caja antes de crear pedidos."
            )
        
        # Descontar inventario
        descontar_inventario(db_pedido, local.id, db)
        
        # Usar puntos si aplica
        if puntos_usar > 0:
            from decimal import Decimal
            exito, mensaje_puntos, movimiento = PuntosService.usar_puntos_en_pedido(
                db, cliente.id, db_pedido.id, puntos_usar, Decimal(str(descuento_puntos))
            )
            if not exito:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al usar puntos: {mensaje_puntos}"
                )
        
        # Otorgar puntos ganados
        if puntos_ganados > 0:
            PuntosService.otorgar_puntos_por_pedido(
                db, cliente.id, db_pedido.id, puntos_ganados,
                f"Puntos ganados por compra directa en {local.nombre}"
            )
        
        # Registrar venta en caja
        registrar_venta_en_caja(db_pedido, current_user.id, db)
        
        # Marcar como ENTREGADO (saltea EN_PREPARACION) o solo CONFIRMADO si requiere delivery
        if requiere_delivery:
            db_pedido.estado_id = estado_confirmado.id
            estado_final_id = estado_confirmado.id
        else:
            db_pedido.estado_id = estado_entregado.id
            estado_final_id = estado_entregado.id
        
        # Marcar como pagado según medio de pago
        _es_diferido = medio_pago.permite_cheque or (medio_pago.plazo_dias or 0) > 0
        if requiere_delivery:
            db_pedido.es_pagado = False
            mensaje_final = f"Pedido creado y confirmado. Pendiente de delivery."
        elif _es_diferido:
            db_pedido.es_pagado = False
            if medio_pago.permite_cheque:
                mensaje_final = f"Pedido creado y entregado. Pendiente de pago con cheque."
            else:
                mensaje_final = f"Pedido creado y entregado. Pago diferido a {medio_pago.plazo_dias} días con {medio_pago.nombre}."
        else:
            db_pedido.es_pagado = True
            mensaje_final = f"Pedido creado, entregado y pagado con {medio_pago.nombre}"

    # NOTA: Para pedidos WEB o CAJAS_VARIABLES, quedan en PENDIENTE
    # Los puntos NO se usan aquí, solo cuando se confirma manualmente

    db.commit()
    db.refresh(db_pedido)

    # 7.5. Ocupar crédito y crear registro de cobro si el pago es diferido
    _es_diferido_post = medio_pago.permite_cheque or (medio_pago.plazo_dias or 0) > 0
    if _es_diferido_post:
        CreditoService.ocupar_credito(cliente.id, monto_total, db)
        # Para pagos diferidos no-cheque, crear CobroPendiente
        if not medio_pago.permite_cheque and (medio_pago.plazo_dias or 0) > 0:
            from datetime import timedelta, timezone as tz
            fecha_venc = db_pedido.fecha_pedido + timedelta(days=medio_pago.plazo_dias)
            monto_cobro = monto_total + float(db_pedido.costo_delivery or 0)
            cobro = CobroPendiente(
                tenant_id=db_pedido.tenant_id,
                pedido_id=db_pedido.id,
                monto=monto_cobro,
                fecha_vencimiento=fecha_venc,
                estado="PENDIENTE",
            )
            db.add(cobro)
            db.commit()
    
    # 8. Retornar respuesta
    return {
        "pedido_id": db_pedido.id,
        "numero_pedido": db_pedido.numero_pedido,
        "monto_total": monto_total,
        "estado": db_pedido.estado_pedido.codigo if db_pedido.estado_pedido else 'PENDIENTE',
        "mensaje": mensaje_final,
        "puntos_ganados": puntos_ganados,
        "puntos_usados": puntos_usar,
        "descuento_puntos": descuento_puntos,
        "auto_confirmado": es_pedido_pos_directo  # Indicador de confirmación automática
    }


@router.get("/estados", response_model=List[dict])
def obtener_estados_pedido(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los estados de pedido configurados.
    
    **Retorna:**
    - Lista de estados con sus propiedades (codigo, nombre, color, orden, es_final)
    
    **Uso:** Frontend (Landing/Backoffice) - Filtros dinámicos, badges, selectores
    """
    from database.models import EstadoPedido as EstadoPedidoModel
    
    estados = db.query(EstadoPedidoModel).filter(
        EstadoPedidoModel.activo == True
    ).order_by(EstadoPedidoModel.orden).all()
    
    return [
        {
            "id": estado.id,
            "codigo": estado.codigo,
            "nombre": estado.nombre,
            "descripcion": estado.descripcion,
            "color": estado.color,
            "orden": estado.orden,
            "es_final": estado.es_final
        }
        for estado in estados
    ]


@router.get("/", response_model=List[PedidoConRelaciones])
def listar_pedidos(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    fecha: str = None,
    tipo_pedido_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los pedidos del tenant con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de pedidos
    """
    from sqlalchemy.orm import joinedload
    from database.models import EstadoPedido as EstadoPedidoModel, Despacho
    
    # Filtrar por tenant y por local asignado al usuario (local_defecto_id)
    # El admin ve todos los locales
    es_admin = current_user.role and current_user.role.nombre.lower() == 'admin'
    filtros_base = [Cliente.tenant_id == current_user.tenant_id]
    if not es_admin and current_user.local_defecto_id:
        filtros_base.append(Pedido.local_id == current_user.local_defecto_id)

    query = db.query(Pedido).join(Cliente).filter(*filtros_base).options(
        joinedload(Pedido.cliente),
        joinedload(Pedido.items).joinedload(ItemPedido.producto),
        joinedload(Pedido.medio_pago),
        joinedload(Pedido.tipo_pedido),
        joinedload(Pedido.tipo_documento_tributario),
        joinedload(Pedido.usuario),
        joinedload(Pedido.estado_pedido),  # Cargar relación de estado
        joinedload(Pedido.cheques)  # Para resumen de cobro
    )
    
    if estado:
        # Filtrar por código de estado
        query = query.join(EstadoPedidoModel, Pedido.estado_id == EstadoPedidoModel.id).filter(
            EstadoPedidoModel.codigo == estado
        )

    if fecha:
        from sqlalchemy import cast, Date
        query = query.filter(cast(Pedido.fecha_pedido, Date) == fecha)

    if tipo_pedido_id:
        query = query.filter(Pedido.tipo_pedido_id == tipo_pedido_id)
    
    pedidos = query.order_by(Pedido.fecha_pedido.desc()).offset(skip).limit(limit).all()

    # Calcular peso total por item desde asignaciones_picking (consulta directa)
    from sqlalchemy import func as sqlfunc
    from database.models import AsignacionPicking
    all_item_ids = [item.id for p in pedidos for item in p.items]
    peso_por_item: dict = {}
    if all_item_ids:
        peso_rows = db.query(
            AsignacionPicking.item_pedido_id,
            sqlfunc.sum(AsignacionPicking.peso_real).label('total_kg')
        ).filter(
            AsignacionPicking.item_pedido_id.in_(all_item_ids)
        ).group_by(AsignacionPicking.item_pedido_id).all()
        peso_por_item = {row.item_pedido_id: float(row.total_kg) for row in peso_rows}

    # Mapear a schema de respuesta
    result = []
    for pedido in pedidos:
        # Verificar si el pedido tiene despacho asignado
        despacho = db.query(Despacho).filter(Despacho.pedido_id == pedido.id).first()
        
        pedido_dict = {
            'id': pedido.id,
            'cliente_id': pedido.cliente_id,
            'cliente_nombre': pedido.cliente.nombre if pedido.cliente else None,  # Para frontend
            'local_id': pedido.local_id,
            'local_despacho_id': pedido.local_despacho_id,
            'numero_pedido': pedido.numero_pedido,
            'fecha_pedido': pedido.fecha_pedido,
            'total': pedido.monto_total,
            'monto_total': pedido.monto_total,  # Alias para compatibilidad
            'estado': pedido.estado_pedido.codigo if pedido.estado_pedido else None,
            'pagado': pedido.es_pagado,
            'inventario_descontado': pedido.inventario_descontado,
            'notas': pedido.notas,
            'notas_admin': pedido.notas_admin,
            # Información del despacho (NUEVO)
            'despacho': {
                'id': despacho.id,
                'estado': despacho.estado_despacho.value if despacho.estado_despacho else None,
                'fecha_asignacion': despacho.fecha_asignacion
            } if despacho else None,
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
            # Información del usuario que creó el pedido
            'usuario_id': pedido.usuario_id,
            'usuario_nombre': pedido.usuario.nombre_completo if pedido.usuario else None,
            'usuario_email': pedido.usuario.email if pedido.usuario else None,
            # Resumen de cobro de cheques (estado_id=3 es COBRADO)
            'monto_cobrado_cheques': sum(float(c.monto) for c in pedido.cheques if c.estado_id == 3) if pedido.cheques else 0.0,
            # Serializar cliente correctamente
            'cliente': {
                'id': pedido.cliente.id,
                'nombre': pedido.cliente.nombre,
                'email': pedido.cliente.email,
                'telefono': pedido.cliente.telefono,
                'rut': pedido.cliente.rut,
                'direccion': pedido.cliente.direccion,
                # 'comuna' eliminado porque ya no existe en Cliente
                'limite_credito': float(pedido.cliente.limite_credito) if pedido.cliente.limite_credito else 0,
                'credito_usado': float(pedido.cliente.credito_usado) if pedido.cliente.credito_usado else 0
            } if pedido.cliente else None,
            # Serializar items correctamente
            'items': [{
                'id': item.id,
                'pedido_id': item.pedido_id,
                'producto_id': item.producto_id,
                'producto_nombre': item.producto.nombre if item.producto else None,
                'cantidad': item.cantidad,
                'precio_unitario_venta': float(item.precio_unitario_venta) if item.precio_unitario_venta else 0,
                'subtotal': float(item.cantidad * item.precio_unitario_venta) if item.cantidad and item.precio_unitario_venta else 0,
                'peso_total_kg': peso_por_item.get(item.id),
            } for item in pedido.items] if pedido.items else []
        }
        result.append(pedido_dict)
    
    return result


@router.get("/{pedido_id}", response_model=PedidoConRelaciones)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Obtiene un pedido por ID del tenant.
    
    **Uso:** Backoffice - Detalle de pedido
    """
    # Filtrar por tenant mediante join con Cliente
    pedido = db.query(Pedido).join(Cliente).filter(
        Pedido.id == pedido_id,
        Cliente.tenant_id == current_user.tenant_id
    ).first()
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
        'numero_pedido': pedido.numero_pedido,
        'fecha_pedido': pedido.fecha_pedido,
        'total': pedido.monto_total,
        'estado': pedido.estado_pedido.codigo if pedido.estado_pedido else None,
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
        # Control SII (Facturación Electrónica)
        'tipo_documento_tributario_id': pedido.tipo_documento_tributario_id,
        'tipo_documento_codigo': pedido.tipo_documento_tributario.codigo if pedido.tipo_documento_tributario else None,
        'tipo_documento_nombre': pedido.tipo_documento_tributario.nombre if pedido.tipo_documento_tributario else None,
        # Información de puntos
        'puntos_ganados': pedido.puntos_ganados,
        'puntos_usados': pedido.puntos_usados,
        'descuento_puntos': float(pedido.descuento_puntos) if pedido.descuento_puntos else None,
        # Información del usuario que creó el pedido
        'usuario_id': pedido.usuario_id,
        'usuario_nombre': pedido.usuario.nombre_completo if pedido.usuario else None,
        'usuario_email': pedido.usuario.email if pedido.usuario else None,
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
    Actualiza el estado de un pedido del tenant y gestiona el inventario.
    
    **Lógica de inventario:**
    - Si cambia a CONFIRMADO y se proporciona local_despacho_id → Descuenta inventario
    - Si cambia a CANCELADO y había inventario descontado → Devuelve inventario
    
    **Uso:** Backoffice - Cambiar estado del pedido
    """
    # Cargar estados desde BD para trabajar con IDs
    from database.models import EstadoPedido as EstadoPedidoModel
    estados_dict = {}
    estados_bd = db.query(EstadoPedidoModel).all()
    for est in estados_bd:
        estados_dict[est.codigo] = est.id
    
    # Obtener IDs de estados clave
    ID_PENDIENTE = estados_dict.get('PENDIENTE')
    ID_CONFIRMADO = estados_dict.get('CONFIRMADO')
    ID_EN_PREPARACION = estados_dict.get('EN_PREPARACION')
    ID_ENTREGADO = estados_dict.get('ENTREGADO')
    ID_CANCELADO = estados_dict.get('CANCELADO')
    
    # Filtrar por tenant mediante join con Cliente
    pedido = db.query(Pedido).join(Cliente).filter(
        Pedido.id == pedido_id,
        Cliente.tenant_id == current_user.tenant_id
    ).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    estado_anterior_id = pedido.estado_id
    estado_anterior_obj = db.query(EstadoPedidoModel).filter(EstadoPedidoModel.id == estado_anterior_id).first()
    estado_anterior_codigo = estado_anterior_obj.codigo if estado_anterior_obj else None
    
    # Actualizar campos básicos
    if pedido_update.pagado is not None:
        pedido.es_pagado = pedido_update.pagado
    if pedido_update.notas_admin is not None:
        pedido.notas_admin = pedido_update.notas_admin
    
    # Actualizar medio de pago (permite asignar cuando estaba NULL)
    if pedido_update.medio_pago_id is not None:
        # Verificar que el medio de pago exista
        from database.models import MedioPago
        medio_pago = db.query(MedioPago).filter(MedioPago.id == pedido_update.medio_pago_id).first()
        if not medio_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medio de pago con ID {pedido_update.medio_pago_id} no encontrado"
            )
        pedido.medio_pago_id = pedido_update.medio_pago_id
    
    # Gestión de inventario según cambio de estado
    if pedido_update.estado:
        nuevo_estado_codigo = pedido_update.estado.value
        nuevo_estado_id = estados_dict.get(nuevo_estado_codigo)
        
        if not nuevo_estado_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado '{nuevo_estado_codigo}' no válido"
            )
        
        # Si cambia a CONFIRMADO
        if nuevo_estado_id == ID_CONFIRMADO and estado_anterior_id != ID_CONFIRMADO:
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
            
            # Verificar que haya un turno de caja abierto SOLO para pedidos POS directos
            # EXCEPCIÓN 1: El local WEB (Tienda Online) no requiere caja abierta
            # EXCEPCIÓN 2: Pedidos creados desde Backoffice/Web (local_id = WEB) no requieren caja
            local_despacho_obj = db.query(Local).filter(Local.id == local_despacho_final).first()
            local_origen_obj = db.query(Local).filter(Local.id == pedido.local_id).first()
            
            # Solo validar caja abierta si:
            # 1. El local de DESPACHO es físico (no WEB)
            # 2. Y el local ORIGEN también es físico (no WEB)
            # Esto excluye pedidos web/backoffice que se confirman posteriormente
            es_pedido_pos_directo = (
                local_despacho_obj and local_despacho_obj.codigo != 'WEB' and
                local_origen_obj and local_origen_obj.codigo != 'WEB'
            )
            
            if es_pedido_pos_directo:
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
            
            # 🏪 LÓGICA DE FLUJO SEGÚN ORIGEN/TIPO DEL PEDIDO
            # - WEB: Flujo normal (PENDIENTE → CONFIRMADO → EN_PREPARACION → ENTREGADO)
            # - CAJAS: Flujo normal (PENDIENTE → CONFIRMADO → EN_PREPARACION → ENTREGADO)
            # - POS/Tienda (productos regulares): Flujo directo (CONFIRMADO + ENTREGADO automático)
            
            # Obtener el local original del pedido para identificar origen
            local_origen = db.query(Local).filter(Local.id == pedido.local_id).first()
            
            # Aplicar flujo directo SOLO si:
            # 1. NO es pedido WEB (local.codigo != 'WEB')
            # 2. NO es pedido de CAJAS_VARIABLES (debe seguir flujo normal de preparación)
            es_pedido_pos_directo = (
                local_origen and 
                local_origen.codigo != 'WEB' and 
                pedido.tipo_pedido and 
                pedido.tipo_pedido.codigo != 'CAJAS_VARIABLES'
            )
            
            if es_pedido_pos_directo:
                # Es un pedido POS de venta directa (productos regulares en tienda física)
                # Marcar como ENTREGADO automáticamente (se saltea EN_PREPARACION)
                nuevo_estado_id = ID_ENTREGADO  # Cambiar el estado final
                
                # Marcar como pagado automáticamente según medio de pago
                if pedido.medio_pago:
                    _diferido = pedido.medio_pago.permite_cheque or (pedido.medio_pago.plazo_dias or 0) > 0
                    if _diferido:
                        # Pago diferido (cheque o transferencia a plazo): queda impago
                        pedido.es_pagado = False
                    else:
                        # Para efectivo, tarjeta, etc: marcar como pagado
                        pedido.es_pagado = True
                else:
                    # Si no tiene medio de pago definido, asumir pagado
                    pedido.es_pagado = True
        
        # Si cambia a CANCELADO
        elif nuevo_estado_id == ID_CANCELADO and estado_anterior_id != ID_CANCELADO:
            # 🚫 VALIDACIÓN: No se puede cancelar pedidos en preparación o ya entregados
            if estado_anterior_id == ID_EN_PREPARACION:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cancelar un pedido que ya está en preparación. Para cancelar, debe revertir primero a CONFIRMADO."
                )
            
            if estado_anterior_id == ID_ENTREGADO:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cancelar un pedido que ya fue entregado. Los pedidos entregados son definitivos."
                )
            
            # Devolver inventario si había sido descontado
            devolver_inventario(pedido, db)

            # Liberar crédito si el pago era diferido y el pedido no estaba pagado
            if pedido.medio_pago and not pedido.es_pagado:
                _era_diferido = pedido.medio_pago.permite_cheque or (pedido.medio_pago.plazo_dias or 0) > 0
                if _era_diferido:
                    CreditoService.liberar_credito(pedido.cliente_id, float(pedido.monto_total), db)
                    # Anular cobros pendientes asociados
                    for cobro in pedido.cobros_pendientes:
                        if cobro.estado in ("PENDIENTE", "VENCIDO"):
                            cobro.estado = "ANULADO"
            
            # Devolver puntos ganados si habían sido otorgados y el pedido estaba confirmado/entregado
            # Estados que implican confirmación: CONFIRMADO, EN_PREPARACION, ENTREGADO
            estados_confirmados_ids = [ID_CONFIRMADO, ID_EN_PREPARACION, ID_ENTREGADO]
            if estado_anterior_id in estados_confirmados_ids and pedido.puntos_ganados and pedido.puntos_ganados > 0:
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
            
            # Devolver puntos usados si habían sido usados y el pedido estaba confirmado/entregado
            if estado_anterior_id in estados_confirmados_ids and pedido.puntos_usados and pedido.puntos_usados > 0:
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
        
        pedido.estado_id = nuevo_estado_id

        # Para CAJAS_VARIABLES: si el pedido ya estaba marcado como pagado ANTES de la
        # confirmación, generar la comisión ahora que el precio real ya fue fijado.
        if (
            nuevo_estado_id == ID_CONFIRMADO
            and pedido.es_pagado
            and pedido.tipo_pedido
            and pedido.tipo_pedido.codigo == 'CAJAS_VARIABLES'
        ):
            try:
                generar_comision(pedido, db)
            except Exception:
                pass
    elif pedido_update.local_despacho_id and pedido.estado_id == ID_CONFIRMADO and not pedido.inventario_descontado:
        descontar_inventario(pedido, pedido_update.local_despacho_id, db)
    
    # Actualizar local de despacho si se proporciona explícitamente (no auto-asignado)
    if pedido_update.local_despacho_id:
        pedido.local_despacho_id = pedido_update.local_despacho_id

    # Generar comisión si el pedido quedó pagado
    if pedido.es_pagado:
        try:
            generar_comision(pedido, db)
        except Exception:
            pass  # No bloquear la actualización por errores en comisiones

    db.commit()
    db.refresh(pedido)
    
    # Mapear a schema de respuesta
    return {
        'id': pedido.id,
        'cliente_id': pedido.cliente_id,
        'local_id': pedido.local_id,
        'local_despacho_id': pedido.local_despacho_id,
        'tipo_pedido_id': pedido.tipo_pedido_id,
        'numero_pedido': pedido.numero_pedido,
        'fecha_pedido': pedido.fecha_pedido,
        'total': pedido.monto_total,
        'estado': pedido.estado_pedido.codigo if pedido.estado_pedido else None,
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
        # Control SII (Facturación Electrónica)
        'tipo_documento_tributario_id': pedido.tipo_documento_tributario_id,
        'tipo_documento_codigo': pedido.tipo_documento_tributario.codigo if pedido.tipo_documento_tributario else None,
        'tipo_documento_nombre': pedido.tipo_documento_tributario.nombre if pedido.tipo_documento_tributario else None,
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
        numero_pedido = pedido.numero_pedido
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


@router.get("/{pedido_id}/factura")
def generar_factura(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Genera y descarga la factura en PDF de un pedido (tipo FAC).
    """
    from sqlalchemy.orm import joinedload
    from database.models import ConfiguracionLanding, Tenant, AsignacionPicking, Lote
    pedido = db.query(Pedido).options(
        joinedload(Pedido.cliente),
        joinedload(Pedido.tenant).joinedload(Tenant.configuracion_landing),
        joinedload(Pedido.tipo_pedido),
        joinedload(Pedido.items).joinedload(ItemPedido.producto),
        joinedload(Pedido.items).joinedload(ItemPedido.asignaciones_picking).joinedload(AsignacionPicking.lote),
    ).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )

    if pedido.tipo_documento_tributario_id != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido no corresponde a una factura (tipo_documento_tributario_id != 1)"
        )

    try:
        from services.boleta_service import generar_factura_pedido
        pdf_buffer = generar_factura_pedido(pedido)
        numero_pedido = pedido.numero_pedido
        nombre_archivo = f"Factura_{numero_pedido}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la factura: {str(e)}"
        )


@router.put("/{pedido_id}/registrar-folio")
def registrar_folio_sii(
    pedido_id: int,
    folio_sii: str,
    numero_dte: str = "",
    observaciones: str = "",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Registra el folio SII de una factura emitida manualmente en el portal del SII.

    **Flujo:** El usuario ingresa la factura en el SII, obtiene el folio y lo registra aquí.
    Actualiza estado_sii a REGISTRADO.
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )

    if pedido.tipo_documento_tributario_id != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede registrar folio en facturas (tipo_documento = FAC)"
        )

    from datetime import datetime
    pedido.folio_sii = folio_sii
    if numero_dte:
        pedido.numero_dte = numero_dte
    pedido.estado_sii = "REGISTRADO"
    pedido.fecha_envio_sii = datetime.now()
    if observaciones:
        pedido.observaciones_sii = observaciones

    db.commit()
    db.refresh(pedido)

    return {
        "pedido_id": pedido_id,
        "folio_sii": pedido.folio_sii,
        "numero_dte": pedido.numero_dte,
        "estado_sii": pedido.estado_sii,
        "fecha_envio_sii": pedido.fecha_envio_sii,
        "mensaje": f"Folio SII {folio_sii} registrado correctamente"
    }


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


@router.patch("/{pedido_id}/registrar-pago")
def registrar_pago(
    pedido_id: int,
    medio_pago_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Registra el medio de pago de un pedido/factura.
    - CHEQUE (permite_cheque=True): es_pagado=False (pendiente hasta acreditación)
    - Resto: es_pagado=True (pago inmediato)
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido {pedido_id} no encontrado")

    # Validar que la factura tenga folio SII registrado
    if not pedido.folio_sii or not pedido.folio_sii.strip():
        raise HTTPException(
            status_code=400,
            detail="No se puede registrar el pago: la factura no tiene folio SII. "
                   "Primero ingrese la factura al SII y registre el folio."
        )

    medio_pago = db.query(MedioPago).filter(MedioPago.id == medio_pago_id, MedioPago.activo == True).first()
    if not medio_pago:
        raise HTTPException(status_code=404, detail=f"Medio de pago {medio_pago_id} no encontrado")

    # --- Lógica de crédito ---
    nuevo_es_diferido = medio_pago.permite_cheque or (medio_pago.plazo_dias or 0) > 0

    # Si el pedido ya tenía un medio de pago diferido anterior, liberar ese crédito primero
    if pedido.medio_pago_id and pedido.medio_pago_id != medio_pago.id:
        medio_pago_anterior = db.query(MedioPago).filter(MedioPago.id == pedido.medio_pago_id).first()
        if medio_pago_anterior:
            anterior_era_diferido = medio_pago_anterior.permite_cheque or (medio_pago_anterior.plazo_dias or 0) > 0
            if anterior_era_diferido:
                CreditoService.liberar_credito(pedido.cliente_id, float(pedido.monto_total), db)

    if nuevo_es_diferido:
        # Validar que el cliente tiene crédito disponible
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente del pedido no encontrado")

        if not cliente.limite_credito or float(cliente.limite_credito) <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"El cliente '{cliente.nombre}' no tiene línea de crédito configurada. "
                       "Para pago a plazo se requiere un límite de crédito asignado."
            )

        es_valido, mensaje_credito = CreditoService.validar_credito_disponible(
            pedido.cliente_id, float(pedido.monto_total), db
        )
        if not es_valido:
            raise HTTPException(
                status_code=400,
                detail=f"Pago diferido rechazado: {mensaje_credito}"
            )

        # Ocupar crédito
        CreditoService.ocupar_credito(pedido.cliente_id, float(pedido.monto_total), db)

        pedido.medio_pago_id = medio_pago.id
        pedido.es_pagado = False

        # Si es diferido no-cheque, crear CobroPendiente
        if not medio_pago.permite_cheque and (medio_pago.plazo_dias or 0) > 0:
            from datetime import timedelta, timezone as tz
            from datetime import datetime as dt
            fecha_venc = dt.now(tz.utc) + timedelta(days=medio_pago.plazo_dias)
            monto_cobro = float(pedido.monto_total) + float(pedido.costo_delivery or 0)
            cobro = CobroPendiente(
                tenant_id=pedido.tenant_id,
                pedido_id=pedido.id,
                monto=monto_cobro,
                fecha_vencimiento=fecha_venc,
                estado="PENDIENTE",
            )
            db.add(cobro)

        if medio_pago.permite_cheque:
            mensaje = f"Medio de pago registrado como Cheque. Pago pendiente de acreditación."
        else:
            mensaje = f"Pago diferido registrado con {medio_pago.nombre}. Vence en {medio_pago.plazo_dias} días."
    else:
        pedido.medio_pago_id = medio_pago.id
        # Efectivo, transferencia contado, tarjeta, etc.: pago inmediato
        pedido.es_pagado = True
        mensaje = f"Pago registrado con {medio_pago.nombre}."

    # Generar comisión si el pedido quedó pagado
    if pedido.es_pagado:
        try:
            generar_comision(pedido, db)
        except Exception:
            pass  # No bloquear el registro de pago por errores en comisiones

    db.commit()
    db.refresh(pedido)

    return {
        "pedido_id": pedido_id,
        "medio_pago": medio_pago.nombre,
        "medio_pago_codigo": medio_pago.codigo,
        "es_pagado": pedido.es_pagado,
        "permite_cheque": medio_pago.permite_cheque,
        "mensaje": mensaje
    }


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Elimina un pedido completamente.
    
    **Importante:** 
    - Si el pedido tiene inventario descontado, lo devuelve automáticamente
    - Elimina items del pedido y movimientos de puntos asociados
    - Operación IRREVERSIBLE
    
    **Uso:** Backoffice - Eliminar pedidos (admin)
    """
    # Buscar el pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {pedido_id} no encontrado"
        )
    
    # Si tiene inventario descontado, devolverlo
    if pedido.inventario_descontado and pedido.local_despacho_id:
        try:
            devolver_inventario(pedido, db)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al devolver inventario: {str(e)}"
            )
    
    # Eliminar movimientos de puntos asociados
    from database.models import MovimientoPuntos
    db.query(MovimientoPuntos).filter(MovimientoPuntos.pedido_id == pedido_id).delete(synchronize_session=False)
    
    # Eliminar items del pedido (cascade debería hacerlo, pero por seguridad)
    db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido_id).delete(synchronize_session=False)
    
    # Eliminar el pedido
    db.delete(pedido)
    db.commit()
    
    return None
