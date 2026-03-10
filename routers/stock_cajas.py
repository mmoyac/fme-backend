"""
Router para gestión de stock de cajas por proveedor.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import List, Optional

from database.database import get_db
from database.models import StockCajasProveedor, MovimientoStockCajas, Producto, Proveedor, Lote, Enrolamiento, PrecioProveedor
from schemas.stock_cajas import (
    StockCajasProveedorCreate,
    StockCajasProveedorUpdate,
    StockCajasProveedorResponse,
    MovimientoStockCajasCreate,
    MovimientoStockCajasResponse,
    ActualizacionStockCajas,
    ReservaStockCajas,
    ResumenStockCajas
)
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[StockCajasProveedorResponse])
async def listar_stock_cajas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    producto_id: Optional[int] = Query(None),
    proveedor_id: Optional[int] = Query(None),
    solo_con_stock: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Listar stock de cajas por proveedor con filtros opcionales."""
    
    query = db.query(
        StockCajasProveedor.id,
        StockCajasProveedor.producto_id,
        StockCajasProveedor.proveedor_id,
        StockCajasProveedor.cajas_disponibles,
        StockCajasProveedor.cajas_totales_recibidas,
        StockCajasProveedor.cajas_totales_vendidas,
        StockCajasProveedor.fecha_ultima_actualizacion,
        Producto.nombre.label('producto_nombre'),
        Producto.sku.label('producto_sku'),
        Proveedor.nombre.label('proveedor_nombre'),
        Proveedor.rut.label('proveedor_rut')
    ).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).join(
        Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
    ).filter(
        Producto.tenant_id == current_user.tenant_id
    )
    
    # Aplicar filtros
    if producto_id:
        query = query.filter(StockCajasProveedor.producto_id == producto_id)
    
    if proveedor_id:
        query = query.filter(StockCajasProveedor.proveedor_id == proveedor_id)
    
    if solo_con_stock:
        query = query.filter(StockCajasProveedor.cajas_disponibles > 0)
    
    # Ordenar por producto y proveedor
    query = query.order_by(Producto.nombre, Proveedor.nombre)
    
    # Paginación
    stock_items = query.offset(skip).limit(limit).all()
    
    return [
        StockCajasProveedorResponse(
            id=item.id,
            producto_id=item.producto_id,
            proveedor_id=item.proveedor_id,
            cajas_disponibles=item.cajas_disponibles,
            cajas_totales_recibidas=item.cajas_totales_recibidas,
            cajas_totales_vendidas=item.cajas_totales_vendidas,
            fecha_ultima_actualizacion=item.fecha_ultima_actualizacion,
            producto_nombre=item.producto_nombre,
            producto_sku=item.producto_sku,
            proveedor_nombre=item.proveedor_nombre,
            proveedor_rut=item.proveedor_rut
        )
        for item in stock_items
    ]


@router.get("/resumen", response_model=ResumenStockCajas)
async def obtener_resumen_stock(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Obtener resumen general del stock de cajas."""
    
    # Estadísticas generales
    total_productos = db.query(func.count(func.distinct(StockCajasProveedor.producto_id))).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).filter(Producto.tenant_id == current_user.tenant_id).scalar() or 0
    
    total_proveedores = db.query(func.count(func.distinct(StockCajasProveedor.proveedor_id))).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).filter(Producto.tenant_id == current_user.tenant_id).scalar() or 0
    
    total_cajas_disponibles = db.query(func.sum(StockCajasProveedor.cajas_disponibles)).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).filter(Producto.tenant_id == current_user.tenant_id).scalar() or 0
    
    productos_sin_stock = db.query(func.count(StockCajasProveedor.id)).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).filter(
        StockCajasProveedor.cajas_disponibles == 0,
        Producto.tenant_id == current_user.tenant_id
    ).scalar() or 0
    
    # Productos con stock disponible
    productos_con_stock_query = db.query(
        StockCajasProveedor.id,
        StockCajasProveedor.producto_id,
        StockCajasProveedor.proveedor_id,
        StockCajasProveedor.cajas_disponibles,
        StockCajasProveedor.cajas_totales_recibidas,
        StockCajasProveedor.cajas_totales_vendidas,
        StockCajasProveedor.fecha_ultima_actualizacion,
        Producto.nombre.label('producto_nombre'),
        Producto.sku.label('producto_sku'),
        Proveedor.nombre.label('proveedor_nombre'),
        Proveedor.rut.label('proveedor_rut')
    ).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).join(
        Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
    ).filter(
        StockCajasProveedor.cajas_disponibles > 0,
        Producto.tenant_id == current_user.tenant_id
    ).order_by(
        StockCajasProveedor.cajas_disponibles.desc()
    ).limit(20)  # Top 20 con más stock
    
    productos_con_stock = productos_con_stock_query.all()
    
    productos_con_stock_response = [
        StockCajasProveedorResponse(
            id=item.id,
            producto_id=item.producto_id,
            proveedor_id=item.proveedor_id,
            cajas_disponibles=item.cajas_disponibles,
            cajas_totales_recibidas=item.cajas_totales_recibidas,
            cajas_totales_vendidas=item.cajas_totales_vendidas,
            fecha_ultima_actualizacion=item.fecha_ultima_actualizacion,
            producto_nombre=item.producto_nombre,
            producto_sku=item.producto_sku,
            proveedor_nombre=item.proveedor_nombre,
            proveedor_rut=item.proveedor_rut
        )
        for item in productos_con_stock
    ]
    
    return ResumenStockCajas(
        total_productos=total_productos,
        total_proveedores=total_proveedores,
        total_cajas_disponibles=total_cajas_disponibles,
        productos_sin_stock=productos_sin_stock,
        productos_con_stock=productos_con_stock_response
    )


@router.get("/peso-promedio")
async def obtener_peso_promedio_por_producto(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtener peso promedio real de las cajas disponibles por producto/proveedor.
    Calcula el peso promedio basado en los lotes finalizados.
    """
    try:
        # Query muy simple - obtener peso promedio de todos los lotes por producto/proveedor
        peso_promedio_query = db.query(
            Lote.producto_id,
            Enrolamiento.proveedor_id,
            func.avg(Lote.peso_actual).label('peso_promedio_kg'),
            func.count(Lote.id).label('cantidad_cajas'),
            Producto.nombre.label('producto_nombre'),
            Proveedor.nombre.label('proveedor_nombre')
        ).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).join(
            Producto, Lote.producto_id == Producto.id
        ).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Producto.tenant_id == current_user.tenant_id
        ).group_by(
            Lote.producto_id,
            Enrolamiento.proveedor_id,
            Producto.nombre,
            Proveedor.nombre
        ).all()
        
        # Convertir a formato de respuesta
        resultado = []
        for item in peso_promedio_query:
            resultado.append({
                'producto_id': item.producto_id,
                'proveedor_id': item.proveedor_id,
                'producto_nombre': item.producto_nombre,
                'proveedor_nombre': item.proveedor_nombre,
                'peso_promedio_kg': round(float(item.peso_promedio_kg), 2) if item.peso_promedio_kg else 25.0,
                'cantidad_cajas': item.cantidad_cajas
            })
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando peso promedio: {str(e)}")


@router.get("/producto/{producto_id}", response_model=List[StockCajasProveedorResponse])
async def obtener_stock_por_producto(
    producto_id: int,
    solo_con_stock: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Obtener stock de cajas disponibles para un producto específico."""
    
    query = db.query(
        StockCajasProveedor.id,
        StockCajasProveedor.producto_id,
        StockCajasProveedor.proveedor_id,
        StockCajasProveedor.cajas_disponibles,
        StockCajasProveedor.cajas_totales_recibidas,
        StockCajasProveedor.cajas_totales_vendidas,
        StockCajasProveedor.fecha_ultima_actualizacion,
        Producto.nombre.label('producto_nombre'),
        Producto.sku.label('producto_sku'),
        Proveedor.nombre.label('proveedor_nombre'),
        Proveedor.rut.label('proveedor_rut')
    ).join(
        Producto, StockCajasProveedor.producto_id == Producto.id
    ).join(
        Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
    ).filter(
        StockCajasProveedor.producto_id == producto_id,
        Producto.tenant_id == current_user.tenant_id
    )
    
    if solo_con_stock:
        query = query.filter(StockCajasProveedor.cajas_disponibles > 0)
    
    # Ordenar por cantidad de cajas disponibles (descendente)
    query = query.order_by(StockCajasProveedor.cajas_disponibles.desc())
    
    stock_items = query.all()
    
    return [
        StockCajasProveedorResponse(
            id=item.id,
            producto_id=item.producto_id,
            proveedor_id=item.proveedor_id,
            cajas_disponibles=item.cajas_disponibles,
            cajas_totales_recibidas=item.cajas_totales_recibidas,
            cajas_totales_vendidas=item.cajas_totales_vendidas,
            fecha_ultima_actualizacion=item.fecha_ultima_actualizacion,
            producto_nombre=item.producto_nombre,
            producto_sku=item.producto_sku,
            proveedor_nombre=item.proveedor_nombre,
            proveedor_rut=item.proveedor_rut
        )
        for item in stock_items
    ]


@router.get("/lotes-disponibles/{producto_id}")
async def obtener_lotes_disponibles_producto(
    producto_id: int,
    cantidad_requerida: int = Query(..., description="Cantidad de cajas requeridas"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtener lotes específicos disponibles para un producto.
    Devuelve las cajas exactas que se entregarían al cliente con peso y precio real.
    """
    
    try:
        # Query para obtener lotes específicos disponibles para venta del producto
        query = db.query(
            Lote.id,
            Lote.codigo_lote,
            Lote.peso_actual,
            Lote.fecha_vencimiento,
            Lote.lote_proveedor,
            Producto.nombre.label('producto_nombre'),
            Proveedor.nombre.label('proveedor_nombre'),
            Proveedor.id.label('proveedor_id'),
            PrecioProveedor.precio_kg.label('precio_por_kg'),
            PrecioProveedor.precio_minimo_kg.label('precio_minimo_por_kg')
        ).join(
            Producto, Lote.producto_id == Producto.id
        ).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).outerjoin(
            PrecioProveedor, and_(
                PrecioProveedor.producto_id == Lote.producto_id,
                PrecioProveedor.proveedor_id == Enrolamiento.proveedor_id,
                PrecioProveedor.activo == True
            )
        ).filter(
            Lote.producto_id == producto_id,
            Lote.disponible_venta == True,
            Lote.vendido == False,
            Producto.tenant_id == current_user.tenant_id
        ).order_by(
            Lote.fecha_vencimiento.asc()  # FIFO - primero en vencer
        )
        
        lotes_disponibles = query.limit(cantidad_requerida).all()
        
        if not lotes_disponibles:
            return {
                "cajas_disponibles": 0,
                "cajas_requeridas": cantidad_requerida,
                "lotes": [],
                "error": "No hay lotes disponibles para este producto"
            }
        
        # Formatear respuesta con precio calculado
        lotes_resultado = []
        for lote in lotes_disponibles:
            precio_por_kg = float(lote.precio_por_kg) if lote.precio_por_kg else 0
            precio_minimo_por_kg = float(lote.precio_minimo_por_kg) if lote.precio_minimo_por_kg else None
            precio_total = float(lote.peso_actual) * precio_por_kg
            
            lotes_resultado.append({
                'lote_id': lote.id,
                'codigo_lote': lote.codigo_lote,
                'peso_kg': float(lote.peso_actual),
                'precio_por_kg': precio_por_kg,
                'precio_minimo_por_kg': precio_minimo_por_kg,
                'precio_total': round(precio_total, 2),
                'fecha_vencimiento': lote.fecha_vencimiento.isoformat(),
                'lote_proveedor': lote.lote_proveedor,
                'proveedor_nombre': lote.proveedor_nombre,
                'proveedor_id': lote.proveedor_id
            })
        
        precio_base_kg = float(lotes_disponibles[0].precio_por_kg) if lotes_disponibles and lotes_disponibles[0].precio_por_kg else None
        precio_minimo_kg = float(lotes_disponibles[0].precio_minimo_por_kg) if lotes_disponibles and lotes_disponibles[0].precio_minimo_por_kg else None
        return {
            "cajas_disponibles": len(lotes_disponibles),
            "cajas_requeridas": cantidad_requerida,
            "lotes": lotes_resultado,
            "producto_nombre": lotes_disponibles[0].producto_nombre if lotes_disponibles else "",
            "precio_base_kg": precio_base_kg,
            "precio_minimo_kg": precio_minimo_kg,
        }
        
    except Exception as e:
        print(f"Error en obtener_lotes_disponibles_producto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar lotes disponibles: {str(e)}")


@router.post("/actualizar-desde-enrolamiento")
async def actualizar_stock_desde_enrolamiento(
    actualizacion: ActualizacionStockCajas,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Actualizar stock de cajas desde un enrolamiento de recepción."""
    
    # Validar que el producto y proveedor existan
    producto = db.query(Producto).filter(Producto.id == actualizacion.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == actualizacion.proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Buscar o crear el registro de stock
    stock_existente = db.query(StockCajasProveedor).filter(
        and_(
            StockCajasProveedor.producto_id == actualizacion.producto_id,
            StockCajasProveedor.proveedor_id == actualizacion.proveedor_id
        )
    ).first()
    
    cajas_antes = 0
    if stock_existente:
        cajas_antes = stock_existente.cajas_disponibles
        stock_existente.cajas_disponibles += actualizacion.cajas_a_sumar
        stock_existente.cajas_totales_recibidas += actualizacion.cajas_a_sumar
        db.commit()
        db.refresh(stock_existente)
        stock_actual = stock_existente
    else:
        # Crear nuevo registro
        stock_actual = StockCajasProveedor(
            producto_id=actualizacion.producto_id,
            proveedor_id=actualizacion.proveedor_id,
            cajas_disponibles=actualizacion.cajas_a_sumar,
            cajas_totales_recibidas=actualizacion.cajas_a_sumar,
            cajas_totales_vendidas=0
        )
        db.add(stock_actual)
        db.commit()
        db.refresh(stock_actual)
    
    # Registrar el movimiento
    movimiento = MovimientoStockCajas(
        producto_id=actualizacion.producto_id,
        proveedor_id=actualizacion.proveedor_id,
        lote_id=actualizacion.lote_id,
        enrolamiento_id=actualizacion.enrolamiento_id,
        tipo_movimiento="ENTRADA_ENROLAMIENTO",
        cajas_movimiento=actualizacion.cajas_a_sumar,
        cajas_antes=cajas_antes,
        cajas_despues=stock_actual.cajas_disponibles,
        descripcion=actualizacion.descripcion or f"Entrada de {actualizacion.cajas_a_sumar} cajas desde enrolamiento",
        usuario=current_user.email
    )
    db.add(movimiento)
    db.commit()
    
    return {
        "mensaje": f"Stock actualizado exitosamente",
        "producto": producto.nombre,
        "proveedor": proveedor.nombre,
        "cajas_agregadas": actualizacion.cajas_a_sumar,
        "stock_anterior": cajas_antes,
        "stock_actual": stock_actual.cajas_disponibles
    }


@router.post("/reservar-para-pedido")
async def reservar_stock_para_pedido(
    reserva: ReservaStockCajas,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Reservar stock de cajas para un pedido (validar disponibilidad)."""
    
    resultados = []
    items_no_disponibles = []
    
    for item in reserva.items:
        producto_id = item.get("producto_id")
        proveedor_id = item.get("proveedor_id")
        cajas_requeridas = item.get("cajas_requeridas", 0)
        
        # Verificar stock disponible
        stock = db.query(StockCajasProveedor).filter(
            and_(
                StockCajasProveedor.producto_id == producto_id,
                StockCajasProveedor.proveedor_id == proveedor_id
            )
        ).first()
        
        if not stock or stock.cajas_disponibles < cajas_requeridas:
            producto = db.query(Producto).filter(Producto.id == producto_id).first()
            proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
            
            items_no_disponibles.append({
                "producto_id": producto_id,
                "producto_nombre": producto.nombre if producto else "Desconocido",
                "proveedor_id": proveedor_id,
                "proveedor_nombre": proveedor.nombre if proveedor else "Desconocido",
                "cajas_requeridas": cajas_requeridas,
                "cajas_disponibles": stock.cajas_disponibles if stock else 0
            })
        else:
            resultados.append({
                "producto_id": producto_id,
                "proveedor_id": proveedor_id,
                "cajas_requeridas": cajas_requeridas,
                "cajas_disponibles": stock.cajas_disponibles,
                "disponible": True
            })
    
    if items_no_disponibles:
        return {
            "disponible": False,
            "mensaje": "Algunos productos no tienen stock suficiente",
            "items_no_disponibles": items_no_disponibles,
            "items_disponibles": resultados
        }
    
    return {
        "disponible": True,
        "mensaje": "Todos los productos tienen stock disponible",
        "items_disponibles": resultados
    }


@router.get("/movimientos", response_model=List[MovimientoStockCajasResponse])
async def listar_movimientos_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    producto_id: Optional[int] = Query(None),
    proveedor_id: Optional[int] = Query(None),
    tipo_movimiento: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Listar historial de movimientos de stock de cajas."""
    
    query = db.query(
        MovimientoStockCajas.id,
        MovimientoStockCajas.producto_id,
        MovimientoStockCajas.proveedor_id,
        MovimientoStockCajas.lote_id,
        MovimientoStockCajas.enrolamiento_id,
        MovimientoStockCajas.pedido_id,
        MovimientoStockCajas.tipo_movimiento,
        MovimientoStockCajas.cajas_movimiento,
        MovimientoStockCajas.cajas_antes,
        MovimientoStockCajas.cajas_despues,
        MovimientoStockCajas.descripcion,
        MovimientoStockCajas.usuario,
        MovimientoStockCajas.fecha_movimiento,
        Producto.nombre.label('producto_nombre'),
        Proveedor.nombre.label('proveedor_nombre')
    ).join(
        Producto, MovimientoStockCajas.producto_id == Producto.id
    ).join(
        Proveedor, MovimientoStockCajas.proveedor_id == Proveedor.id
    ).filter(
        Producto.tenant_id == current_user.tenant_id
    )
    
    # Aplicar filtros
    if producto_id:
        query = query.filter(MovimientoStockCajas.producto_id == producto_id)
    
    if proveedor_id:
        query = query.filter(MovimientoStockCajas.proveedor_id == proveedor_id)
    
    if tipo_movimiento:
        query = query.filter(MovimientoStockCajas.tipo_movimiento == tipo_movimiento)
    
    # Ordenar por fecha descendente
    query = query.order_by(MovimientoStockCajas.fecha_movimiento.desc())
    
    # Paginación
    movimientos = query.offset(skip).limit(limit).all()
    
    return [
        MovimientoStockCajasResponse(
            id=mov.id,
            producto_id=mov.producto_id,
            proveedor_id=mov.proveedor_id,
            lote_id=mov.lote_id,
            enrolamiento_id=mov.enrolamiento_id,
            pedido_id=mov.pedido_id,
            tipo_movimiento=mov.tipo_movimiento,
            cajas_movimiento=mov.cajas_movimiento,
            cajas_antes=mov.cajas_antes,
            cajas_despues=mov.cajas_despues,
            descripcion=mov.descripcion,
            usuario=mov.usuario,
            fecha_movimiento=mov.fecha_movimiento,
            producto_nombre=mov.producto_nombre,
            proveedor_nombre=mov.proveedor_nombre
        )
        for mov in movimientos
    ]


@router.put("/ajustar/{producto_id}/{proveedor_id}")
async def ajustar_stock_manual(
    producto_id: int,
    proveedor_id: int,
    ajuste: StockCajasProveedorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Realizar ajuste manual del stock de cajas."""
    
    if ajuste.cajas_disponibles is None:
        raise HTTPException(status_code=400, detail="Debe especificar las cajas disponibles")
    
    # Buscar el registro de stock
    stock = db.query(StockCajasProveedor).filter(
        and_(
            StockCajasProveedor.producto_id == producto_id,
            StockCajasProveedor.proveedor_id == proveedor_id
        )
    ).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock no encontrado para este producto y proveedor")
    
    cajas_antes = stock.cajas_disponibles
    diferencia = ajuste.cajas_disponibles - cajas_antes
    
    # Actualizar stock
    stock.cajas_disponibles = ajuste.cajas_disponibles
    db.commit()
    
    # Registrar movimiento
    movimiento = MovimientoStockCajas(
        producto_id=producto_id,
        proveedor_id=proveedor_id,
        tipo_movimiento="AJUSTE_INVENTARIO",
        cajas_movimiento=diferencia,
        cajas_antes=cajas_antes,
        cajas_despues=ajuste.cajas_disponibles,
        descripcion=f"Ajuste manual de stock por {current_user.email}",
        usuario=current_user.email
    )
    db.add(movimiento)
    db.commit()
    
    return {
        "mensaje": "Ajuste de stock realizado exitosamente",
        "stock_anterior": cajas_antes,
        "stock_nuevo": ajuste.cajas_disponibles,
        "diferencia": diferencia
    }


@router.get("/lotes-asignados-pedido/{pedido_id}")
async def obtener_lotes_asignados_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtener los lotes específicos YA ASIGNADOS a un pedido.
    Útil para confirmar pedidos PENDIENTES que ya tienen lotes reservados.
    """
    from database.models import Pedido
    
    # Verificar que el pedido existe y pertenece al tenant
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == current_user.tenant_id
    ).first()
    
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Buscar movimientos de reserva o venta de lotes para este pedido
    movimientos = db.query(MovimientoStockCajas).filter(
        MovimientoStockCajas.referencia_tipo == "PEDIDO",
        MovimientoStockCajas.referencia_id == pedido_id,
        MovimientoStockCajas.tipo_movimiento.in_(["RESERVA_LOTE", "VENTA_LOTE"])
    ).all()
    
    if not movimientos:
        return {
            "pedido_id": pedido_id,
            "tiene_lotes_asignados": False,
            "items": []
        }
    
    # Agrupar por producto
    items_por_producto = {}
    
    for mov in movimientos:
        if mov.lote_codigo:
            # Buscar el lote con su precio
            lote_query = db.query(
                Lote.codigo_lote,
                Lote.peso_actual,
                Lote.fecha_vencimiento,
                Lote.lote_proveedor,
                Lote.disponible_venta,
                Lote.vendido,
                Lote.producto_id,
                Enrolamiento.proveedor_id,
                PrecioProveedor.precio_kg
            ).join(
                Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
            ).outerjoin(
                PrecioProveedor, and_(
                    PrecioProveedor.producto_id == Lote.producto_id,
                    PrecioProveedor.proveedor_id == Enrolamiento.proveedor_id,
                    PrecioProveedor.activo == True
                )
            ).filter(
                Lote.codigo_lote == mov.lote_codigo
            ).first()
            
            if lote_query:
                producto_id = lote_query.producto_id
                proveedor_id = lote_query.proveedor_id
                
                if producto_id not in items_por_producto:
                    producto = db.query(Producto).filter(Producto.id == producto_id).first()
                    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
                    
                    items_por_producto[producto_id] = {
                        "producto_id": producto_id,
                        "producto_nombre": producto.nombre if producto else f"Producto {producto_id}",
                        "proveedor_id": proveedor_id,
                        "proveedor_nombre": proveedor.nombre if proveedor else f"Proveedor {proveedor_id}",
                        "lotes": []
                    }
                
                # Calcular precio del lote
                precio_kg = float(lote_query.precio_kg) if lote_query.precio_kg else 0.0
                peso_kg = float(lote_query.peso_actual)
                precio_total = peso_kg * precio_kg
                
                items_por_producto[producto_id]["lotes"].append({
                    "lote_codigo": lote_query.codigo_lote,
                    "peso_kg": peso_kg,
                    "precio_kg": precio_kg,
                    "precio_total": precio_total,
                    "fecha_vencimiento": lote_query.fecha_vencimiento.isoformat() if lote_query.fecha_vencimiento else None,
                    "lote_proveedor": lote_query.lote_proveedor,
                    "disponible_venta": lote_query.disponible_venta,
                    "vendido": lote_query.vendido,
                    "tipo_movimiento": mov.tipo_movimiento
                })
    
    # Calcular totales
    items = list(items_por_producto.values())
    total_precio_estimado = sum(
        sum(l["precio_total"] for l in item["lotes"])
        for item in items
    )
    
    return {
        "pedido_id": pedido_id,
        "tiene_lotes_asignados": True,
        "items": items,
        "total_precio": total_precio_estimado,
        "cantidad_items": len(items),
        "total_cajas": sum(len(item["lotes"]) for item in items)
    }