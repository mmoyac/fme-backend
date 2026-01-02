"""
Router para endpoints del Dashboard.
Estadísticas y métricas de ventas.
"""
from typing import Dict, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
import pytz

from database.database import get_db
from database.models import Pedido, ItemPedido, Producto, Inventario, Cliente, Local, TurnoCaja, OperacionCaja, User, TipoOperacionCaja, EstadoTurnoCaja

router = APIRouter()

# Zona horaria de Chile
CHILE_TZ = pytz.timezone('America/Santiago')


@router.get("/estadisticas")
def obtener_estadisticas_dashboard(db: Session = Depends(get_db)):
    """
    Obtiene las estadísticas principales para el dashboard.
    
    Retorna:
    - Ventas del día y del mes
    - Total de pedidos por estado
    - Monto y cantidad de pedidos por cobrar
    - Ticket promedio
    - Productos más vendidos
    - Stock bajo
    - Total de clientes
    """
    # Obtener fecha/hora actual en zona horaria de Chile
    ahora_chile = datetime.now(CHILE_TZ)
    hoy = ahora_chile.date()
    inicio_mes = datetime(hoy.year, hoy.month, 1, tzinfo=CHILE_TZ).date()
    hace_7_dias = hoy - timedelta(days=7)
    
    # --- Ventas del día ---
    ventas_hoy = db.query(func.sum(Pedido.monto_total)).filter(
        func.date(Pedido.fecha_pedido) == hoy
    ).scalar() or 0
    
    # --- Ventas del mes ---
    ventas_mes = db.query(func.sum(Pedido.monto_total)).filter(
        func.date(Pedido.fecha_pedido) >= inicio_mes
    ).scalar() or 0
    
    # --- Pedidos pendientes de pago ---
    pedidos_sin_pagar = db.query(Pedido).filter(
        Pedido.es_pagado == False,
        Pedido.estado != 'CANCELADO'
    ).all()
    
    monto_por_cobrar = sum(p.monto_total for p in pedidos_sin_pagar)
    cantidad_sin_pagar = len(pedidos_sin_pagar)
    
    # --- Pedidos por estado ---
    pedidos_por_estado = db.query(
        Pedido.estado,
        func.count(Pedido.id).label('cantidad')
    ).group_by(Pedido.estado).all()
    
    estados = {
        'PENDIENTE': 0,
        'CONFIRMADO': 0,
        'EN_PREPARACION': 0,
        'ENTREGADO': 0,
        'CANCELADO': 0
    }
    
    for estado, cantidad in pedidos_por_estado:
        estados[estado] = cantidad
    
    total_pedidos = sum(estados.values())
    
    # --- Ticket promedio ---
    if total_pedidos > 0:
        ticket_promedio = ventas_mes / total_pedidos
    else:
        ticket_promedio = 0
    
    # --- Productos más vendidos (top 5) ---
    productos_mas_vendidos = db.query(
        Producto.nombre,
        Producto.sku,
        func.sum(ItemPedido.cantidad).label('total_vendido')
    ).join(ItemPedido, Producto.id == ItemPedido.producto_id)\
     .join(Pedido, Pedido.id == ItemPedido.pedido_id)\
     .filter(Pedido.estado != 'CANCELADO')\
     .group_by(Producto.id, Producto.nombre, Producto.sku)\
     .order_by(func.sum(ItemPedido.cantidad).desc())\
     .limit(5)\
     .all()
    
    top_productos = [
        {
            'nombre': p.nombre,
            'sku': p.sku,
            'cantidad_vendida': int(p.total_vendido)
        }
        for p in productos_mas_vendidos
    ]
    
    # --- Stock bajo (menos de 10 unidades totales) ---
    stock_bajo = db.query(
        Producto.nombre,
        Producto.sku,
        func.sum(Inventario.cantidad_stock).label('stock_total')
    ).join(Inventario, Producto.id == Inventario.producto_id)\
     .join(Local, Local.id == Inventario.local_id)\
     .filter(Local.codigo != 'WEB')\
     .group_by(Producto.id, Producto.nombre, Producto.sku)\
     .having(func.sum(Inventario.cantidad_stock) < 10)\
     .order_by(func.sum(Inventario.cantidad_stock))\
     .limit(5)\
     .all()
    
    productos_stock_bajo = [
        {
            'nombre': p.nombre,
            'sku': p.sku,
            'stock': int(p.stock_total)
        }
        for p in stock_bajo
    ]
    
    # --- Clientes nuevos (últimos 7 días) ---
    # Nota: Cliente no tiene campo fecha_creacion, se usa conteo total por ahora
    total_clientes = db.query(func.count(Cliente.id)).scalar() or 0
    
    # --- Ventas por día (últimos 7 días) ---
    # --- Ventas por día (últimos 7 días) ---
    ventas_por_dia = []
    for i in range(7):
        fecha = hoy - timedelta(days=6-i)
        ventas_dia = db.query(func.sum(Pedido.monto_total)).filter(
            func.date(Pedido.fecha_pedido) == fecha
        ).scalar() or 0
        
        ventas_por_dia.append({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'dia': fecha.strftime('%a'),
            'ventas': float(ventas_dia)
        })
    
    # --- Últimos pedidos (5 más recientes) ---
    ultimos_pedidos = db.query(Pedido).order_by(Pedido.fecha_pedido.desc()).limit(5).all()
    
    pedidos_recientes = [
        {
            'id': p.id,
            'numero_pedido': f"PED-{p.id:05d}",
            'cliente': p.cliente.nombre if p.cliente else 'N/A',
            'monto': float(p.monto_total),
            'estado': p.estado,
            'fecha': p.fecha_pedido.astimezone(CHILE_TZ).strftime('%Y-%m-%d %H:%M')
        }
        for p in ultimos_pedidos
    ]
    
    # --- MÉTRICAS DE CAJA (RESUMEN) ---
    # Turnos abiertos actualmente
    turnos_abiertos_count = db.query(func.count(TurnoCaja.id)).filter(
        TurnoCaja.estado == EstadoTurnoCaja.ABIERTO
    ).scalar() or 0
    
    # Ventas de caja del día (desde operaciones de caja)
    ventas_caja_hoy = db.query(func.sum(OperacionCaja.monto)).filter(
        func.date(OperacionCaja.fecha_operacion) == hoy,
        OperacionCaja.tipo_operacion == TipoOperacionCaja.VENTA
    ).scalar() or 0
    
    # Diferencias de cuadre pendientes (turnos cerrados con diferencia != 0)
    diferencias_pendientes = db.query(func.count(TurnoCaja.id)).filter(
        TurnoCaja.estado == EstadoTurnoCaja.CERRADO,
        func.date(TurnoCaja.fecha_cierre) >= hace_7_dias,
        TurnoCaja.diferencia != 0
    ).scalar() or 0
    
    return {
        'ventas': {
            'hoy': float(ventas_hoy),
            'mes': float(ventas_mes)
        },
        'pedidos': {
            'total': total_pedidos,
            'por_estado': estados
        },
        'por_cobrar': {
            'monto': float(monto_por_cobrar),
            'cantidad': cantidad_sin_pagar
        },
        'ticket_promedio': float(ticket_promedio),
        'top_productos': top_productos,
        'stock_bajo': productos_stock_bajo,
        'total_clientes': total_clientes,
        'ventas_por_dia': ventas_por_dia,
        'ultimos_pedidos': pedidos_recientes,
        'caja': {
            'turnos_abiertos': turnos_abiertos_count,
            'ventas_hoy': float(ventas_caja_hoy),
            'diferencias_pendientes': diferencias_pendientes
        }
    }


@router.get("/metricas-caja")
def obtener_metricas_caja(db: Session = Depends(get_db)):
    """
    Obtiene métricas específicas del sistema de caja.
    
    Retorna:
    - Turnos abiertos por local
    - Ventas por vendedor del día
    - Diferencias en cuadres recientes
    - Resumen de operaciones por tipo
    """
    # Obtener fecha actual en zona horaria de Chile
    ahora_chile = datetime.now(CHILE_TZ)
    hoy = ahora_chile.date()
    
    # --- Turnos abiertos por local ---
    turnos_abiertos = db.query(
        TurnoCaja.id,
        TurnoCaja.local_id,
        Local.nombre.label('local_nombre'),
        TurnoCaja.vendedor_id,
        User.nombre_completo.label('vendedor_nombre'),
        TurnoCaja.fecha_apertura,
        TurnoCaja.monto_inicial
    ).join(Local, TurnoCaja.local_id == Local.id)\
     .join(User, TurnoCaja.vendedor_id == User.id)\
     .filter(TurnoCaja.estado == EstadoTurnoCaja.ABIERTO)\
     .all()
    
    turnos_info = []
    for turno in turnos_abiertos:
        # Calcular total de operaciones para este turno
        total_operaciones = db.query(func.sum(OperacionCaja.monto)).filter(
            OperacionCaja.turno_caja_id == turno.id,
            OperacionCaja.tipo_operacion == TipoOperacionCaja.VENTA
        ).scalar() or 0
        
        turnos_info.append({
            'turno_id': turno.id,
            'local_id': turno.local_id,
            'local_nombre': turno.local_nombre,
            'vendedor_id': turno.vendedor_id,
            'vendedor_nombre': turno.vendedor_nombre,
            'fecha_apertura': turno.fecha_apertura.strftime('%Y-%m-%d %H:%M:%S'),
            'monto_inicial': float(turno.monto_inicial),
            'ventas_acumuladas': float(total_operaciones),
            'efectivo_esperado': float(turno.monto_inicial + total_operaciones)
        })
    
    # --- Ventas por vendedor del día ---
    ventas_por_vendedor = db.query(
        User.id,
        User.nombre_completo,
        func.count(OperacionCaja.id).label('num_ventas'),
        func.sum(OperacionCaja.monto).label('total_ventas')
    ).join(TurnoCaja, User.id == TurnoCaja.vendedor_id)\
     .join(OperacionCaja, TurnoCaja.id == OperacionCaja.turno_caja_id)\
     .filter(
         func.date(OperacionCaja.fecha_operacion) == hoy,
         OperacionCaja.tipo_operacion == TipoOperacionCaja.VENTA
     ).group_by(User.id, User.nombre_completo)\
     .order_by(func.sum(OperacionCaja.monto).desc())\
     .limit(10)\
     .all()
    
    vendedores_stats = [
        {
            'vendedor_id': v.id,
            'vendedor_nombre': v.nombre_completo,
            'num_ventas': v.num_ventas,
            'total_ventas': float(v.total_ventas or 0)
        }
        for v in ventas_por_vendedor
    ]
    
    # --- Diferencias en cuadres recientes (últimos 7 días) ---
    hace_7_dias = hoy - timedelta(days=7)
    diferencias_cuadre = db.query(
        TurnoCaja.id,
        TurnoCaja.fecha_cierre,
        Local.nombre.label('local_nombre'),
        User.nombre_completo.label('vendedor_nombre'),
        TurnoCaja.efectivo_esperado,
        TurnoCaja.efectivo_real,
        TurnoCaja.diferencia
    ).join(Local, TurnoCaja.local_id == Local.id)\
     .join(User, TurnoCaja.vendedor_id == User.id)\
     .filter(
         TurnoCaja.estado == EstadoTurnoCaja.CERRADO,
         func.date(TurnoCaja.fecha_cierre) >= hace_7_dias,
         TurnoCaja.diferencia != 0
     ).order_by(TurnoCaja.fecha_cierre.desc())\
     .limit(15)\
     .all()
    
    diferencias_info = [
        {
            'turno_id': d.id,
            'fecha_cierre': d.fecha_cierre.strftime('%Y-%m-%d %H:%M:%S'),
            'local_nombre': d.local_nombre,
            'vendedor_nombre': d.vendedor_nombre,
            'efectivo_esperado': float(d.efectivo_esperado or 0),
            'efectivo_real': float(d.efectivo_real or 0),
            'diferencia': float(d.diferencia or 0),
            'tipo_diferencia': 'sobrante' if (d.diferencia or 0) > 0 else 'faltante'
        }
        for d in diferencias_cuadre
    ]
    
    # --- Resumen de operaciones por tipo (últimos 30 días) ---
    hace_30_dias = hoy - timedelta(days=30)
    resumen_operaciones = db.query(
        OperacionCaja.tipo_operacion,
        func.count(OperacionCaja.id).label('cantidad'),
        func.sum(OperacionCaja.monto).label('total_monto')
    ).filter(
        func.date(OperacionCaja.fecha_operacion) >= hace_30_dias
    ).group_by(OperacionCaja.tipo_operacion)\
     .all()
    
    operaciones_resumen = [
        {
            'tipo': op.tipo_operacion.value,
            'cantidad': op.cantidad,
            'total_monto': float(op.total_monto or 0)
        }
        for op in resumen_operaciones
    ]
    
    # --- Estadísticas generales ---
    total_turnos_activos = len(turnos_abiertos)
    total_vendedores_activos_hoy = len(vendedores_stats)
    
    return {
        'fecha_consulta': hoy.isoformat(),
        'turnos_abiertos': {
            'total': total_turnos_activos,
            'detalle': turnos_info
        },
        'ventas_por_vendedor_hoy': {
            'total_vendedores_activos': total_vendedores_activos_hoy,
            'detalle': vendedores_stats
        },
        'diferencias_cuadre_recientes': {
            'total_con_diferencia': len(diferencias_info),
            'detalle': diferencias_info
        },
        'resumen_operaciones_30d': {
            'por_tipo': operaciones_resumen,
            'total_operaciones': sum(op['cantidad'] for op in operaciones_resumen)
        }
    }
