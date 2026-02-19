"""
Router para utilidades administrativas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.database import get_db
from routers.auth import get_current_active_user

router = APIRouter()


@router.post("/reset-sequences", status_code=status.HTTP_200_OK)
def resetear_secuencias(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Resetea todas las secuencias de IDs a 1.
    
    **Uso:** Después de limpiar completamente la base de datos.
    **Requiere:** Permisos de administrador
    """
    
    # Lista de secuencias a resetear
    secuencias = [
        'productos_id_seq',
        'clientes_id_seq',
        'pedidos_id_seq',
        'items_pedido_id_seq',
        'inventario_id_seq',
        'precios_id_seq',
        'movimientos_inventario_id_seq',
        'ordenes_produccion_id_seq',
        'detalles_orden_produccion_id_seq',
        'compras_id_seq',
        'detalles_compra_id_seq',
        'puntos_cliente_id_seq',
        'movimientos_puntos_id_seq',
        'recetas_id_seq',
        'ingredientes_receta_id_seq',
        'informacion_nutricional_id_seq',
        'producto_sellos_id_seq',
        'stock_cajas_proveedor_id_seq',
        'lotes_caja_id_seq',
        'movimientos_stock_cajas_id_seq',
        'turnos_caja_id_seq',
        'operaciones_caja_id_seq',
        'despachos_id_seq',
        'picking_items_id_seq',
        'cheques_id_seq'
    ]
    
    resetadas = 0
    errores = []
    
    for secuencia in secuencias:
        try:
            sql = text(f"ALTER SEQUENCE {secuencia} RESTART WITH 1")
            db.execute(sql)
            db.commit()  # Commit inmediato después de cada secuencia exitosa
            resetadas += 1
        except Exception as e:
            db.rollback()  # Rollback para limpiar la transacción fallida
            errores.append(f"{secuencia}: {str(e)[:100]}")
    
    return {
        "message": f"Secuencias reseteadas: {resetadas}/{len(secuencias)}",
        "resetadas": resetadas,
        "total": len(secuencias),
        "errores": errores if errores else None
    }
