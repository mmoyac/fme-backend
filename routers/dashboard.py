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
from database.models import Pedido, ItemPedido, Producto, Inventario, Cliente, Local

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
        'ultimos_pedidos': pedidos_recientes
    }
