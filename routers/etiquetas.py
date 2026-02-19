"""
Router para gestión de Etiquetas Nutricionales y Sellos de Advertencia.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database.models import SelloAdvertencia, InformacionNutricional, Producto, ProductoSello
from schemas.etiquetas import (
    SelloAdvertenciaResponse,
    InformacionNutricionalCreate,
    InformacionNutricionalUpdate,
    InformacionNutricionalResponse,
    EtiquetaProductoResponse,
    AsignarSellosRequest
)
from routers.auth import get_current_active_user

router = APIRouter(prefix="/api/etiquetas", tags=["Etiquetas"])


# ===========================
# Sellos de Advertencia
# ===========================

@router.get("/sellos", response_model=List[SelloAdvertenciaResponse])
def listar_sellos(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Listar todos los sellos de advertencia disponibles."""
    sellos = db.query(SelloAdvertencia).filter(SelloAdvertencia.activo == True).order_by(SelloAdvertencia.orden).all()
    return sellos


# ===========================
# Información Nutricional
# ===========================

@router.get("/producto/{producto_id}/nutricional", response_model=InformacionNutricionalResponse)
def obtener_info_nutricional(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Obtener la información nutricional de un producto."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Obtener info nutricional
    info = db.query(InformacionNutricional).filter(
        InformacionNutricional.producto_id == producto_id
    ).first()
    
    if not info:
        raise HTTPException(status_code=404, detail="El producto no tiene información nutricional configurada")
    
    return info


@router.post("/producto/{producto_id}/nutricional", response_model=InformacionNutricionalResponse)
def crear_info_nutricional(
    producto_id: int,
    data: InformacionNutricionalCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Crear información nutricional para un producto."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Verificar que no exista ya
    existe = db.query(InformacionNutricional).filter(
        InformacionNutricional.producto_id == producto_id
    ).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="El producto ya tiene información nutricional. Use PUT para actualizar.")
    
    # Crear
    info = InformacionNutricional(
        producto_id=producto_id,
        **data.model_dump(exclude={'producto_id'})
    )
    db.add(info)
    db.commit()
    db.refresh(info)
    
    return info


@router.put("/producto/{producto_id}/nutricional", response_model=InformacionNutricionalResponse)
def actualizar_info_nutricional(
    producto_id: int,
    data: InformacionNutricionalUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Actualizar información nutricional de un producto."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Obtener info nutricional
    info = db.query(InformacionNutricional).filter(
        InformacionNutricional.producto_id == producto_id
    ).first()
    
    if not info:
        raise HTTPException(status_code=404, detail="El producto no tiene información nutricional. Use POST para crear.")
    
    # Actualizar campos proporcionados
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(info, field, value)
    
    db.commit()
    db.refresh(info)
    
    return info


@router.delete("/producto/{producto_id}/nutricional")
def eliminar_info_nutricional(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Eliminar información nutricional de un producto."""
    info = db.query(InformacionNutricional).filter(
        InformacionNutricional.producto_id == producto_id
    ).first()
    
    if not info:
        raise HTTPException(status_code=404, detail="Información nutricional no encontrada")
    
    db.delete(info)
    db.commit()
    
    return {"message": "Información nutricional eliminada exitosamente"}


# ===========================
# Sellos de Producto
# ===========================

@router.post("/producto/{producto_id}/sellos")
def asignar_sellos(
    producto_id: int,
    request: AsignarSellosRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Asignar sellos de advertencia a un producto (reemplaza los existentes)."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Eliminar sellos actuales
    db.query(ProductoSello).filter(ProductoSello.producto_id == producto_id).delete()
    
    # Agregar nuevos sellos
    for sello_id in request.sello_ids:
        # Verificar que el sello existe
        sello = db.query(SelloAdvertencia).filter(SelloAdvertencia.id == sello_id).first()
        if not sello:
            raise HTTPException(status_code=404, detail=f"Sello {sello_id} no encontrado")
        
        producto_sello = ProductoSello(
            producto_id=producto_id,
            sello_id=sello_id
        )
        db.add(producto_sello)
    
    db.commit()
    
    return {"message": f"{len(request.sello_ids)} sellos asignados exitosamente"}


@router.get("/producto/{producto_id}/sellos", response_model=List[SelloAdvertenciaResponse])
def obtener_sellos_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Obtener los sellos asignados a un producto."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Obtener sellos
    producto_sellos = db.query(ProductoSello).filter(
        ProductoSello.producto_id == producto_id
    ).all()
    
    sellos = [
        db.query(SelloAdvertencia).filter(SelloAdvertencia.id == ps.sello_id).first()
        for ps in producto_sellos
    ]
    
    return [s for s in sellos if s]  # Filtrar None


# ===========================
# Etiqueta Completa
# ===========================

@router.get("/producto/{producto_id}/completa", response_model=EtiquetaProductoResponse)
def obtener_etiqueta_completa(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Obtener toda la información de etiqueta de un producto (nutricional + sellos)."""
    # Obtener producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Obtener info nutricional (puede ser None)
    info_nutricional = db.query(InformacionNutricional).filter(
        InformacionNutricional.producto_id == producto_id
    ).first()
    
    # Obtener sellos
    producto_sellos = db.query(ProductoSello).filter(
        ProductoSello.producto_id == producto_id
    ).all()
    
    sellos = [
        db.query(SelloAdvertencia).filter(SelloAdvertencia.id == ps.sello_id).first()
        for ps in producto_sellos
    ]
    sellos = [s for s in sellos if s]  # Filtrar None
    
    return {
        "producto_id": producto.id,
        "producto_nombre": producto.nombre,
        "producto_sku": producto.sku,
        "codigo_barra": producto.codigo_barra,
        "informacion_nutricional": info_nutricional,
        "sellos": sellos
    }
