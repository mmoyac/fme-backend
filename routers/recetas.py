"""
Router para gestión de Recetas e Ingredientes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from database.database import get_db
from database.models import Receta as RecetaModel, IngredienteReceta as IngredienteRecetaModel, Producto, UnidadMedida, User
from schemas.receta import (
    RecetaCreate, RecetaUpdate, RecetaResponse, RecetaConDetalles,
    IngredienteRecetaCreate, IngredienteRecetaUpdate, IngredienteRecetaResponse
)
from routers.auth import get_current_active_user

router = APIRouter()


def calcular_costos_receta(receta: RecetaModel, db: Session):
    """Calcula los costos de una receta basándose en sus ingredientes."""
    costo_total = Decimal('0')
    
    for ingrediente in receta.ingredientes:
        producto_ingrediente = db.query(Producto).filter(Producto.id == ingrediente.producto_ingrediente_id).first()
        
        if producto_ingrediente:
            # Usar precio_compra si es materia prima, o costo_fabricacion si es producto elaborado
            costo_unitario = producto_ingrediente.precio_compra or producto_ingrediente.costo_fabricacion or Decimal('0')
            
            # Calcular costo total del ingrediente
            costo_ingrediente = costo_unitario * ingrediente.cantidad
            
            # Actualizar ingrediente
            ingrediente.costo_unitario_referencia = costo_unitario
            ingrediente.costo_total_calculado = costo_ingrediente
            
            costo_total += costo_ingrediente
    
    # Actualizar receta
    receta.costo_total_calculado = costo_total
    receta.costo_unitario_calculado = costo_total / receta.rendimiento if receta.rendimiento > 0 else Decimal('0')
    
    db.commit()
    
    # Actualizar el costo_fabricacion del producto
    producto = db.query(Producto).filter(Producto.id == receta.producto_id).first()
    if producto:
        producto.costo_fabricacion = receta.costo_unitario_calculado
        db.commit()
    
    return receta


# ============================================
# RECETAS
# ============================================

@router.get("/productos/{producto_id}/receta", response_model=RecetaResponse)
def obtener_receta_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener la receta activa de un producto."""
    receta = db.query(RecetaModel).filter(
        RecetaModel.producto_id == producto_id,
        RecetaModel.activa == True
    ).first()
    
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    return receta


@router.post("/productos/{producto_id}/receta", response_model=RecetaResponse, status_code=status.HTTP_201_CREATED)
def crear_receta(
    producto_id: int,
    receta_data: RecetaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear una nueva receta para un producto."""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Desactivar recetas anteriores
    db.query(RecetaModel).filter(
        RecetaModel.producto_id == producto_id,
        RecetaModel.activa == True
    ).update({"activa": False})
    
    # Crear nueva receta
    receta_dict = receta_data.model_dump(exclude={'ingredientes'})
    receta_dict['producto_id'] = producto_id
    
    db_receta = RecetaModel(**receta_dict)
    db.add(db_receta)
    db.flush()  # Para obtener el ID
    
    # Agregar ingredientes
    for ing_data in receta_data.ingredientes:
        ing_dict = ing_data.model_dump()
        ing_dict['receta_id'] = db_receta.id
        
        db_ingrediente = IngredienteRecetaModel(**ing_dict)
        db.add(db_ingrediente)
    
    db.commit()
    db.refresh(db_receta)
    
    # Calcular costos
    calcular_costos_receta(db_receta, db)
    
    # Marcar producto como "tiene_receta"
    producto.tiene_receta = True
    db.commit()
    
    db.refresh(db_receta)
    return db_receta


@router.put("/recetas/{receta_id}", response_model=RecetaResponse)
def actualizar_receta(
    receta_id: int,
    receta_data: RecetaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar una receta existente."""
    db_receta = db.query(RecetaModel).filter(RecetaModel.id == receta_id).first()
    if not db_receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    update_data = receta_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_receta, field, value)
    
    db.commit()
    
    # Recalcular costos
    calcular_costos_receta(db_receta, db)
    
    db.refresh(db_receta)
    return db_receta


@router.delete("/recetas/{receta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_receta(
    receta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar una receta."""
    db_receta = db.query(RecetaModel).filter(RecetaModel.id == receta_id).first()
    if not db_receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    producto_id = db_receta.producto_id
    
    db.delete(db_receta)
    db.commit()
    
    # Verificar si quedan recetas para este producto
    tiene_recetas = db.query(RecetaModel).filter(RecetaModel.producto_id == producto_id).count() > 0
    
    # Actualizar flag del producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        producto.tiene_receta = tiene_recetas
        if not tiene_recetas:
            producto.costo_fabricacion = None
        db.commit()
    
    return None


# ============================================
# INGREDIENTES
# ============================================

@router.post("/recetas/{receta_id}/ingredientes", response_model=IngredienteRecetaResponse, status_code=status.HTTP_201_CREATED)
def agregar_ingrediente(
    receta_id: int,
    ingrediente: IngredienteRecetaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Agregar un ingrediente a una receta."""
    # Verificar que la receta existe
    receta = db.query(RecetaModel).filter(RecetaModel.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    # Crear ingrediente
    ing_dict = ingrediente.model_dump()
    ing_dict['receta_id'] = receta_id
    
    db_ingrediente = IngredienteRecetaModel(**ing_dict)
    db.add(db_ingrediente)
    db.commit()
    db.refresh(db_ingrediente)
    
    # Recalcular costos de la receta
    calcular_costos_receta(receta, db)
    
    # Refrescar la receta para que incluya el nuevo ingrediente
    db.refresh(receta)
    
    return db_ingrediente


@router.put("/ingredientes/{ingrediente_id}", response_model=IngredienteRecetaResponse)
def actualizar_ingrediente(
    ingrediente_id: int,
    ingrediente: IngredienteRecetaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar un ingrediente de una receta."""
    db_ingrediente = db.query(IngredienteRecetaModel).filter(IngredienteRecetaModel.id == ingrediente_id).first()
    if not db_ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    
    update_data = ingrediente.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ingrediente, field, value)
    
    db.commit()
    db.refresh(db_ingrediente)
    
    # Recalcular costos de la receta
    receta = db.query(RecetaModel).filter(RecetaModel.id == db_ingrediente.receta_id).first()
    if receta:
        calcular_costos_receta(receta, db)
    
    return db_ingrediente


@router.delete("/ingredientes/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ingrediente(
    ingrediente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar un ingrediente de una receta."""
    db_ingrediente = db.query(IngredienteRecetaModel).filter(IngredienteRecetaModel.id == ingrediente_id).first()
    if not db_ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    
    receta_id = db_ingrediente.receta_id
    
    db.delete(db_ingrediente)
    db.commit()
    
    # Recalcular costos de la receta
    receta = db.query(RecetaModel).filter(RecetaModel.id == receta_id).first()
    if receta:
        calcular_costos_receta(receta, db)
    
    return None


@router.post("/recetas/{receta_id}/recalcular", response_model=RecetaResponse)
def recalcular_costos(
    receta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Recalcular los costos de una receta manualmente."""
    receta = db.query(RecetaModel).filter(RecetaModel.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    calcular_costos_receta(receta, db)
    db.refresh(receta)
    
    return receta
