"""
Servicio para consultas de inventario.
Lógica de negocio para consultas de disponibilidad y stock.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import Inventario, Producto, Local, Precio


def get_catalogo_web(db: Session) -> List[dict]:
    """
    Obtiene el catálogo de productos con precios del local WEB.
    Stock total = suma de locales físicos (excluye Tienda Online)
    
    Returns:
        Lista de productos con SKU, nombre, descripción, precio y stock total
    """
    # Primero obtenemos el ID del local WEB
    local_web = db.query(Local).filter(Local.codigo == 'WEB').first()
    if not local_web:
        return []
    
    resultados = (
        db.query(
            Producto.sku,
            Producto.nombre,
            Producto.descripcion,
            Producto.imagen_url,
            Precio.monto_precio.label('precio'),
            func.coalesce(func.sum(Inventario.cantidad_stock), 0).label('stock_total')
        )
        .join(Precio, (Precio.producto_id == Producto.id) & (Precio.local_id == local_web.id))
        .outerjoin(Inventario, Inventario.producto_id == Producto.id)
        .outerjoin(Local, Local.id == Inventario.local_id)
        .filter((Local.codigo != 'WEB') | (Local.codigo == None))
        .group_by(Producto.id, Producto.sku, Producto.nombre, Producto.descripcion, Producto.imagen_url, Precio.monto_precio)
        .order_by(Producto.nombre)
        .all()
    )
    
    return [
        {
            "sku": r.sku,
            "nombre": r.nombre,
            "descripcion": r.descripcion or "",
            "imagen_url": r.imagen_url,
            "precio": float(r.precio),
            "stock_total": int(r.stock_total)
        }
        for r in resultados
    ]


def get_resumen_inventario(db: Session) -> List[dict]:
    """
    Obtiene el resumen de inventario: todos los productos con su stock total.
    Stock total = suma de locales físicos (excluye Tienda Online)
    
    Returns:
        Lista de productos con SKU, nombre y stock total
    """
    resultados = (
        db.query(
            Producto.sku,
            Producto.nombre,
            func.sum(Inventario.cantidad_stock).label('stock_total')
        )
        .join(Inventario, Producto.id == Inventario.producto_id)
        .join(Local, Local.id == Inventario.local_id)
        .filter(Local.codigo != 'WEB')
        .group_by(Producto.id, Producto.sku, Producto.nombre)
        .order_by(Producto.nombre)
        .all()
    )
    
    return [
        {
            "sku": r.sku,
            "nombre": r.nombre,
            "stock_total": r.stock_total or 0
        }
        for r in resultados
    ]


def get_detalle_inventario_by_sku(db: Session, sku: str) -> Optional[dict]:
    """
    Obtiene el detalle de inventario de un producto por SKU.
    Muestra el stock en cada local.
    
    Args:
        db: Sesión de base de datos
        sku: SKU del producto
        
    Returns:
        Diccionario con información del producto y detalle por local
        None si el producto no existe
    """
    # Obtener el producto
    producto = db.query(Producto).filter(Producto.sku == sku).first()
    
    if not producto:
        return None
    
    # Obtener inventario por local (solo locales físicos, excluye WEB)
    inventarios = (
        db.query(
            Local.nombre,
            Local.direccion,
            Inventario.cantidad_stock
        )
        .join(Inventario, Local.id == Inventario.local_id)
        .filter(Inventario.producto_id == producto.id)
        .filter(Local.codigo != 'WEB')
        .order_by(Local.nombre)
        .all()
    )
    
    # Calcular stock total
    stock_total = sum(inv.cantidad_stock for inv in inventarios)
    
    # Construir respuesta
    detalle_locales = [
        {
            "local": inv.nombre,
            "direccion": inv.direccion or "",
            "stock": inv.cantidad_stock
        }
        for inv in inventarios
    ]
    
    return {
        "sku": producto.sku,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion or "",
        "stock_total": stock_total,
        "detalle_locales": detalle_locales
    }
