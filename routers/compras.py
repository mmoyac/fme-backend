from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime

from database.database import get_db
from database import models
from schemas import compras as schemas
from routers.auth import get_current_active_user

router = APIRouter(
    prefix="/compras",
    tags=["Compras"]
)

# -----------------------------------------------------------------------------
# Proveedores
# -----------------------------------------------------------------------------

@router.get("/proveedores", response_model=List[schemas.ProveedorRead])
def get_proveedores(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return db.query(models.Proveedor).options(
        joinedload(models.Proveedor.tipo_proveedor)
    ).filter(
        models.Proveedor.tenant_id == current_user.tenant_id
    ).order_by(models.Proveedor.nombre).all()

@router.post("/proveedores", response_model=schemas.ProveedorRead)
def create_proveedor(proveedor: schemas.ProveedorCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        db_prov = models.Proveedor(**proveedor.model_dump(), tenant_id=current_user.tenant_id)
        db.add(db_prov)
        db.commit()
        db.refresh(db_prov)
        return db_prov
    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig)
        
        # Detectar error de RUT duplicado (único por tenant)
        if 'uix_proveedor_tenant_rut' in error_message or 'ix_proveedores_rut' in error_message or 'duplicate key' in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"El RUT '{proveedor.rut}' ya está registrado para este tenant"
            )
        
        # Detectar error de email duplicado
        if 'ix_proveedores_email' in error_message or 'email' in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"El email '{proveedor.email}' ya está registrado"
            )
        
        # Error genérico de integridad
        raise HTTPException(status_code=400, detail="Error de integridad en los datos")

@router.put("/proveedores/{proveedor_id}", response_model=schemas.ProveedorRead)
def update_proveedor(proveedor_id: int, proveedor: schemas.ProveedorUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_prov = db.query(models.Proveedor).filter(
        models.Proveedor.id == proveedor_id,
        models.Proveedor.tenant_id == current_user.tenant_id
    ).first()
    if not db_prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    for key, value in proveedor.model_dump(exclude_unset=True).items():
        setattr(db_prov, key, value)
    
    db.commit()
    db.refresh(db_prov)
    return db_prov

# -----------------------------------------------------------------------------
# Compras
# -----------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.CompraRead])
def get_compras(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return db.query(models.Compra).join(models.Local).filter(
        models.Local.tenant_id == current_user.tenant_id
    ).order_by(models.Compra.id.desc()).all()

@router.get("/{compra_id}", response_model=schemas.CompraRead)
def get_compra(compra_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    compra = db.query(models.Compra).join(models.Local).filter(
        models.Compra.id == compra_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return compra

@router.post("/", response_model=schemas.CompraRead)
def create_compra(compra: schemas.CompraCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    # Validar que el local pertenezca al tenant
    local = db.query(models.Local).filter(
        models.Local.id == compra.local_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local no encontrado o no pertenece a tu organización")
    
    # 1. Crear Cabecera (Estado PENDIENTE)
    nueva_compra = models.Compra(
        proveedor_id=compra.proveedor_id,
        local_id=compra.local_id,
        fecha_compra=compra.fecha_compra or datetime.now(),
        numero_documento=compra.numero_documento,
        tipo_documento_id=compra.tipo_documento_id,
        notas=compra.notas,
        estado="PENDIENTE",
        monto_total=0
    )
    db.add(nueva_compra)
    db.flush()

    total_compra = 0

    # 2. Guardar Detalles (Sin afectar inventario aun)
    for det in compra.detalles:
        nuevo_detalle = models.DetalleCompra(
            compra_id=nueva_compra.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario
        )
        db.add(nuevo_detalle)
        
        line_total = float(det.cantidad) * float(det.precio_unitario)
        total_compra += line_total
    
    nueva_compra.monto_total = total_compra
    db.commit()
    db.refresh(nueva_compra)
    return nueva_compra

@router.put("/{compra_id}", response_model=schemas.CompraRead)
def update_compra(compra_id: int, compra_data: schemas.CompraCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_compra = db.query(models.Compra).join(models.Local).filter(
        models.Compra.id == compra_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    if db_compra.estado == "RECIBIDA":
        raise HTTPException(status_code=400, detail="No se puede modificar una compra ya recibida")

    # Actualizar cabecera
    db_compra.proveedor_id = compra_data.proveedor_id
    db_compra.local_id = compra_data.local_id
    db_compra.fecha_compra = compra_data.fecha_compra or db_compra.fecha_compra
    db_compra.numero_documento = compra_data.numero_documento
    db_compra.tipo_documento_id = compra_data.tipo_documento_id
    db_compra.notas = compra_data.notas

    # Eliminar detalles anteriores
    db.query(models.DetalleCompra).filter(models.DetalleCompra.compra_id == compra_id).delete()
    
    # Crear nuevos detalles
    total_compra = 0
    for det in compra_data.detalles:
        nuevo_detalle = models.DetalleCompra(
            compra_id=db_compra.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario
        )
        db.add(nuevo_detalle)
        line_total = float(det.cantidad) * float(det.precio_unitario)
        total_compra += line_total
    
    db_compra.monto_total = total_compra
    db.commit()
    db.refresh(db_compra)
    return db_compra

@router.delete("/{compra_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_compra(
    compra_id: int, 
    force: bool = False,  # Parámetro para forzar eliminación
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_active_user)
):
    """
    Elimina una compra.
    
    Por defecto, no permite eliminar compras RECIBIDAS (que ya afectaron stock).
    Use force=true para eliminar cualquier compra (útil para resets completos).
    """
    db_compra = db.query(models.Compra).join(models.Local).filter(
        models.Compra.id == compra_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Validar si es RECIBIDA y no se está forzando
    if db_compra.estado == "RECIBIDA" and not force:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar una compra ya recibida (afectó stock). Use force=true para eliminar de todos modos."
        )

    db.delete(db_compra)
    db.commit()
    return None

@router.post("/{compra_id}/recibir", response_model=schemas.CompraRead)
def recibir_compra(compra_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Cambia el estado de la compra a RECIBIDA y actualiza el inventario.
    """
    db_compra = db.query(models.Compra).join(models.Local).filter(
        models.Compra.id == compra_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    if db_compra.estado == "RECIBIDA":
        raise HTTPException(status_code=400, detail="La compra ya fue recibida")

    # Procesar Inventario y Costos
    for det in db_compra.detalles:
        # A. Actualizar Inventario
        inventario = db.query(models.Inventario).filter(
            models.Inventario.producto_id == det.producto_id,
            models.Inventario.local_id == db_compra.local_id
        ).first()

        if not inventario:
            inventario = models.Inventario(
                producto_id=det.producto_id,
                local_id=db_compra.local_id,
                cantidad_stock=0
            )
            db.add(inventario)
        
        inventario.cantidad_stock = float(inventario.cantidad_stock) + float(det.cantidad)

        # B. Actualizar Costo del Producto (Precio Compra)
        producto = db.query(models.Producto).filter(models.Producto.id == det.producto_id).first()
        if producto:
            producto.precio_compra = det.precio_unitario
    
    db_compra.estado = "RECIBIDA"
    db.commit()
    db.refresh(db_compra)
    return db_compra
