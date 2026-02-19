"""
Router para gestión de precios por proveedor
Específico para productos de caja variable (carnes)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from database.database import get_db
from database.models import PrecioProveedor, Producto, Proveedor, User
from schemas.precios_proveedor import (
    PrecioProveedorCreate,
    PrecioProveedorUpdate, 
    PrecioProveedorResponse,
    PrecioProveedorConDetalles,
    ProductoPreciosProveedores,
    ProveedorPreciosProductos
)
from routers.auth import get_current_active_user

router = APIRouter(tags=["Precios por Proveedor"])

# ============================================
# CRUD BÁSICO DE PRECIOS
# ============================================

@router.get("/", response_model=List[PrecioProveedorConDetalles])
def listar_precios_proveedor(
    producto_id: Optional[int] = Query(None, description="Filtrar por producto"),
    proveedor_id: Optional[int] = Query(None, description="Filtrar por proveedor"),
    solo_activos: bool = Query(True, description="Solo precios activos"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar precios de proveedor con filtros opcionales."""
    query = db.query(PrecioProveedor).options(
        joinedload(PrecioProveedor.producto),
        joinedload(PrecioProveedor.proveedor)
    ).join(
        Producto, PrecioProveedor.producto_id == Producto.id
    ).filter(
        Producto.tenant_id == current_user.tenant_id
    )
    
    # Aplicar filtros
    if producto_id:
        query = query.filter(PrecioProveedor.producto_id == producto_id)
    if proveedor_id:
        query = query.filter(PrecioProveedor.proveedor_id == proveedor_id)
    if solo_activos:
        query = query.filter(PrecioProveedor.activo == True)
    
    precios = query.offset(skip).limit(limit).all()
    
    # Formatear respuesta
    resultado = []
    for precio in precios:
        resultado.append({
            "id": precio.id,
            "producto_id": precio.producto_id,
            "proveedor_id": precio.proveedor_id,
            "precio_kg": float(precio.precio_kg),
            "fecha_vigencia": precio.fecha_vigencia,
            "activo": precio.activo,
            "notas": precio.notas,
            "producto_nombre": precio.producto.nombre,
            "producto_sku": precio.producto.sku,
            "proveedor_nombre": precio.proveedor.nombre,
            "proveedor_rut": precio.proveedor.rut
        })
    
    return resultado


@router.post("/", response_model=PrecioProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_precio_proveedor(
    precio: PrecioProveedorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear un nuevo precio por proveedor."""
    # Verificar que producto y proveedor existen
    producto = db.query(Producto).filter(Producto.id == precio.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    proveedor = db.query(Proveedor).filter(Proveedor.id == precio.proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Verificar si ya existe un precio activo para esta combinación
    precio_existente = db.query(PrecioProveedor).filter(
        PrecioProveedor.producto_id == precio.producto_id,
        PrecioProveedor.proveedor_id == precio.proveedor_id,
        PrecioProveedor.activo == True
    ).first()
    
    if precio_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un precio activo para {producto.nombre} del proveedor {proveedor.nombre}"
        )
    
    # Crear nuevo precio
    db_precio = PrecioProveedor(**precio.model_dump())
    db.add(db_precio)
    db.commit()
    db.refresh(db_precio)
    
    return db_precio


@router.put("/{precio_id}", response_model=PrecioProveedorResponse)
def actualizar_precio_proveedor(
    precio_id: int,
    precio_update: PrecioProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar un precio existente."""
    db_precio = db.query(PrecioProveedor).filter(PrecioProveedor.id == precio_id).first()
    if not db_precio:
        raise HTTPException(status_code=404, detail="Precio no encontrado")
    
    # Actualizar campos proporcionados
    update_data = precio_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_precio, field, value)
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.delete("/{precio_id}")
def eliminar_precio_proveedor(
    precio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar (desactivar) un precio por proveedor."""
    db_precio = db.query(PrecioProveedor).filter(PrecioProveedor.id == precio_id).first()
    if not db_precio:
        raise HTTPException(status_code=404, detail="Precio no encontrado")
    
    # Desactivar en lugar de eliminar para mantener historial
    db_precio.activo = False
    db.commit()
    
    return {"message": "Precio desactivado correctamente"}


# ============================================
# ENDPOINTS ESPECIALIZADOS
# ============================================

@router.get("/productos", response_model=List[ProductoPreciosProveedores])
def listar_productos_con_precios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar todos los productos con sus precios por proveedor."""
    productos = db.query(Producto).filter(
        Producto.tenant_id == current_user.tenant_id
    ).all()
    resultado = []
    
    for producto in productos:
        precios_proveedor = db.query(PrecioProveedor).options(
            joinedload(PrecioProveedor.proveedor)
        ).filter(
            PrecioProveedor.producto_id == producto.id,
            PrecioProveedor.activo == True
        ).all()
        
        precios_formateados = []
        for precio in precios_proveedor:
            precios_formateados.append({
                "id": precio.id,
                "producto_id": precio.producto_id,
                "proveedor_id": precio.proveedor_id,
                "precio_kg": float(precio.precio_kg),
                "fecha_vigencia": precio.fecha_vigencia,
                "activo": precio.activo,
                "notas": precio.notas,
                "producto_nombre": producto.nombre,
                "producto_sku": producto.sku,
                "proveedor_nombre": precio.proveedor.nombre,
                "proveedor_rut": precio.proveedor.rut
            })
        
        resultado.append({
            "id": producto.id,
            "nombre": producto.nombre,
            "sku": producto.sku,
            "precios_proveedores": precios_formateados
        })
    
    return resultado


@router.get("/proveedor/{proveedor_id}/precio/{producto_id}")
def obtener_precio_especifico(
    proveedor_id: int,
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener precio específico de un producto para un proveedor."""
    precio = db.query(PrecioProveedor).filter(
        PrecioProveedor.proveedor_id == proveedor_id,
        PrecioProveedor.producto_id == producto_id,
        PrecioProveedor.activo == True
    ).first()
    
    if not precio:
        raise HTTPException(
            status_code=404, 
            detail="No existe precio configurado para este producto y proveedor"
        )
    
    return {
        "precio_kg": float(precio.precio_kg),
        "fecha_vigencia": precio.fecha_vigencia,
        "notas": precio.notas
    }


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def crear_precios_masivos(
    precios: List[PrecioProveedorCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear múltiples precios de una vez."""
    errores = []
    creados = []
    
    for i, precio in enumerate(precios):
        try:
            # Verificar duplicados
            precio_existente = db.query(PrecioProveedor).filter(
                PrecioProveedor.producto_id == precio.producto_id,
                PrecioProveedor.proveedor_id == precio.proveedor_id,
                PrecioProveedor.activo == True
            ).first()
            
            if precio_existente:
                errores.append({
                    "index": i,
                    "error": f"Ya existe precio activo para producto {precio.producto_id} y proveedor {precio.proveedor_id}"
                })
                continue
            
            db_precio = PrecioProveedor(**precio.model_dump())
            db.add(db_precio)
            db.flush()  # Para obtener el ID sin commit
            creados.append(db_precio.id)
            
        except Exception as e:
            errores.append({
                "index": i,
                "error": str(e)
            })
    
    if errores:
        db.rollback()
        return {
            "message": "Algunos precios no pudieron ser creados",
            "errores": errores,
            "creados": []
        }
    
    db.commit()
    return {
        "message": f"Se crearon {len(creados)} precios correctamente",
        "creados": creados,
        "errores": []
    }