from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.database import get_db
from database import models
from schemas import compras as schemas

router = APIRouter(
    prefix="/compras",
    tags=["Compras"]
)

# -----------------------------------------------------------------------------
# Proveedores
# -----------------------------------------------------------------------------

@router.get("/proveedores", response_model=List[schemas.ProveedorRead])
def get_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).order_by(models.Proveedor.nombre).all()

@router.post("/proveedores", response_model=schemas.ProveedorRead)
def create_proveedor(proveedor: schemas.ProveedorCreate, db: Session = Depends(get_db)):
    db_prov = models.Proveedor(**proveedor.dict())
    db.add(db_prov)
    db.commit()
    db.refresh(db_prov)
    return db_prov

@router.put("/proveedores/{proveedor_id}", response_model=schemas.ProveedorRead)
def update_proveedor(proveedor_id: int, proveedor: schemas.ProveedorUpdate, db: Session = Depends(get_db)):
    db_prov = db.query(models.Proveedor).filter(models.Proveedor.id == proveedor_id).first()
    if not db_prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    for key, value in proveedor.dict(exclude_unset=True).items():
        setattr(db_prov, key, value)
    
    db.commit()
    db.refresh(db_prov)
    return db_prov

# -----------------------------------------------------------------------------
# Compras
# -----------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.CompraRead])
def get_compras(db: Session = Depends(get_db)):
    return db.query(models.Compra).order_by(models.Compra.id.desc()).all()

@router.get("/{compra_id}", response_model=schemas.CompraRead)
def get_compra(compra_id: int, db: Session = Depends(get_db)):
    compra = db.query(models.Compra).filter(models.Compra.id == compra_id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return compra

@router.post("/", response_model=schemas.CompraRead)
def create_compra(compra: schemas.CompraCreate, db: Session = Depends(get_db)):
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
def update_compra(compra_id: int, compra_data: schemas.CompraCreate, db: Session = Depends(get_db)):
    db_compra = db.query(models.Compra).filter(models.Compra.id == compra_id).first()
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
def delete_compra(compra_id: int, db: Session = Depends(get_db)):
    db_compra = db.query(models.Compra).filter(models.Compra.id == compra_id).first()
    if not db_compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    if db_compra.estado == "RECIBIDA":
        raise HTTPException(status_code=400, detail="No se puede eliminar una compra ya recibida (afectó stock)")

    db.delete(db_compra)
    db.commit()
    return None

@router.post("/{compra_id}/recibir", response_model=schemas.CompraRead)
def recibir_compra(compra_id: int, db: Session = Depends(get_db)):
    """
    Cambia el estado de la compra a RECIBIDA y actualiza el inventario.
    """
    db_compra = db.query(models.Compra).filter(models.Compra.id == compra_id).first()
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
