"""
Router para endpoints de Inventario.
Consultas de disponibilidad y stock.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Inventario, Producto, Local, MovimientoInventario
from schemas.inventario_consulta import InventarioResumen, InventarioDetalle
from schemas.inventario import InventarioResponse, InventarioUpdate
from services import inventario_service
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/resumen", response_model=List[InventarioResumen])
def obtener_resumen_inventario(db: Session = Depends(get_db)):
    """
    Obtiene el resumen de inventario de todos los productos.
    
    Retorna una lista con:
    - SKU del producto
    - Nombre del producto
    - Stock total (suma de todos los locales)
    
    **Ideal para:** Listar productos disponibles en un chat o interfaz
    """
    resumen = inventario_service.get_resumen_inventario(db)
    return resumen


@router.get("/detalle/{sku}", response_model=InventarioDetalle)
def obtener_detalle_inventario(
    sku: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el detalle de inventario de un producto específico por SKU.
    
    Retorna:
    - Información del producto (SKU, nombre, descripción)
    - Stock total
    - Detalle de stock por cada local (nombre, dirección, cantidad)
    
    **Ideal para:** Mostrar disponibilidad por sucursal cuando el usuario pregunta por un producto
    
    - **sku**: Código SKU del producto a consultar
    """
    detalle = inventario_service.get_detalle_inventario_by_sku(db, sku)
    
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con SKU '{sku}' no encontrado"
        )
    
    return detalle


# --------------------------------------------------
# CRUD Endpoints para Backoffice
# --------------------------------------------------

@router.get("/", response_model=List[InventarioResponse])
def listar_inventario(
    skip: int = 0,
    limit: int = 100,
    producto_id: int = None,
    local_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista registros de inventario del tenant con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de inventario
    """
    # Unir con Producto para filtrar por tenant_id
    query = db.query(Inventario).join(Producto).filter(Producto.tenant_id == current_user.tenant_id)
    
    if producto_id:
        query = query.filter(Inventario.producto_id == producto_id)
    if local_id:
        query = query.filter(Inventario.local_id == local_id)
    
    inventarios = query.offset(skip).limit(limit).all()
    return inventarios


@router.get("/producto/{producto_id}/local/{local_id}", response_model=dict)
def obtener_inventario_producto_local(
    producto_id: int,
    local_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el stock de un producto específico en un local específico.
    
    **Uso:** Frontend - Para mostrar stock disponible al crear pedidos
    """
    inventario = db.query(Inventario).filter(
        Inventario.producto_id == producto_id,
        Inventario.local_id == local_id
    ).first()
    
    if not inventario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe inventario para producto {producto_id} en local {local_id}"
        )
    
    return {
        "producto_id": inventario.producto_id,
        "local_id": inventario.local_id,
        "cantidad_stock": inventario.cantidad_stock
    }


@router.put("/{inventario_id}", response_model=InventarioResponse)
def actualizar_inventario(
    inventario_id: int,
    inventario: InventarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza el stock de un registro de inventario del tenant.
    
    **Uso:** Backoffice - Ajustar stock
    """
    # Validar que el inventario pertenece al tenant
    db_inventario = db.query(Inventario).join(Producto).filter(
        Inventario.id == inventario_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not db_inventario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventario con ID {inventario_id} no encontrado"
        )
    
    # Actualizar stock
    if inventario.cantidad_stock is not None:
        db_inventario.cantidad_stock = inventario.cantidad_stock
    
    db.commit()
    db.refresh(db_inventario)
    return db_inventario


@router.put("/producto/{producto_id}/local/{local_id}", response_model=InventarioResponse)
def actualizar_inventario_por_producto_local(
    producto_id: int,
    local_id: int,
    inventario_data: InventarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza o crea el stock de un producto en un local específico del tenant.
    
    **Uso:** Backoffice - Ajustar stock por producto/local
    """
    # Verificar que producto y local existan y pertenezcan al tenant
    producto = db.query(Producto).filter(Producto.id == producto_id, Producto.tenant_id == current_user.tenant_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Buscar o crear inventario
    db_inventario = db.query(Inventario).filter(
        Inventario.producto_id == producto_id,
        Inventario.local_id == local_id
    ).first()
    
    if db_inventario:
        # Actualizar existente
        db_inventario.cantidad_stock = inventario_data.cantidad_stock
    else:
        # Crear nuevo
        db_inventario = Inventario(
            producto_id=producto_id,
            local_id=local_id,
            cantidad_stock=inventario_data.cantidad_stock
        )
        db.add(db_inventario)
    
    db.commit()
    db.refresh(db_inventario)
    return db_inventario


@router.post("/ajuste-merma")
def ajuste_merma(
    producto_id: int,
    local_id: int,
    cantidad: int,
    motivo: str = "",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Descuenta stock por merma (pérdida, daño, vencimiento).
    - Solo permite descuentos (cantidad > 0).
    - No puede dejar stock negativo.
    - Registra el movimiento tipo MERMA con el usuario que lo realizó.
    """
    if cantidad <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad a descontar debe ser mayor a cero"
        )

    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    local = db.query(Local).filter(
        Local.id == local_id,
        Local.tenant_id == current_user.tenant_id
    ).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local no encontrado")

    db_inventario = db.query(Inventario).filter(
        Inventario.producto_id == producto_id,
        Inventario.local_id == local_id
    ).first()
    if not db_inventario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe inventario para ese producto/local")

    if cantidad > db_inventario.cantidad_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La cantidad a descontar ({cantidad}) supera el stock disponible ({db_inventario.cantidad_stock})"
        )

    stock_anterior = db_inventario.cantidad_stock
    db_inventario.cantidad_stock = max(0, db_inventario.cantidad_stock - cantidad)

    movimiento = MovimientoInventario(
        producto_id=producto_id,
        local_origen_id=local_id,
        local_destino_id=None,
        cantidad=cantidad,
        tipo_movimiento="MERMA",
        notas=motivo or f"Merma registrada por {current_user.nombre_completo or current_user.email}",
        usuario=current_user.nombre_completo or current_user.email
    )
    db.add(movimiento)
    db.commit()
    db.refresh(db_inventario)

    return {
        "producto_id": producto_id,
        "local_id": local_id,
        "stock_anterior": stock_anterior,
        "cantidad_descontada": cantidad,
        "stock_nuevo": db_inventario.cantidad_stock,
        "usuario": current_user.nombre_completo or current_user.email
    }
