"""
Router para gestión de Recetas e Ingredientes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from database.database import get_db
from database.models import Receta as RecetaModel, IngredienteReceta as IngredienteRecetaModel, Producto, UnidadMedida, User
from schemas.receta import (
    RecetaCreate, RecetaUpdate, RecetaResponse, RecetaConDetalles,
    IngredienteRecetaCreate, IngredienteRecetaUpdate, IngredienteRecetaResponse
)
from routers.auth import get_current_active_user

router = APIRouter()


# Límite de las columnas de costo Numeric(10,2)
MAX_COSTO = Decimal("99999999.99")


def _a_dinero(valor: Decimal) -> Decimal:
    """Redondea a 2 decimales (escala de las columnas de costo) y valida el rango.

    Evita el `numeric field overflow` de Postgres al persistir Decimals de alta
    precisión en columnas Numeric(10,2).
    """
    try:
        q = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Valor de costo inválido en el cálculo de la receta")
    if abs(q) > MAX_COSTO:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Un costo calculado ({q}) excede el máximo permitido ({MAX_COSTO}). "
                "Revisa cantidades, precios o rendimiento."
            ),
        )
    return q


def _div_segura(numerador: Decimal, denominador) -> Decimal:
    """División que trata un denominador nulo/cero como 1 (evita ZeroDivision)."""
    den = Decimal(denominador or 1)
    if den == 0:
        den = Decimal(1)
    return numerador / den


def calcular_costos_receta(receta: RecetaModel, db: Session):
    """Calcula los costos de una receta basándose en sus ingredientes.

    Solo muta objetos en la sesión (no hace commit): la atomicidad la controla el
    endpoint que la invoca. Todos los costos se redondean a 2 decimales antes de
    asignarse para no exceder la precisión de las columnas.
    """
    costo_total = Decimal('0')

    for ingrediente in receta.ingredientes:
        producto_ingrediente = db.query(Producto).filter(Producto.id == ingrediente.producto_ingrediente_id).first()
        unidad_base = db.query(UnidadMedida).filter(UnidadMedida.id == producto_ingrediente.unidad_medida_id).first() if producto_ingrediente else None
        unidad_ingrediente = db.query(UnidadMedida).filter(UnidadMedida.id == ingrediente.unidad_medida_id).first() if ingrediente.unidad_medida_id else None

        # Precio: precio_compra si es materia prima, o costo_fabricacion si es elaborado
        precio_por_unidad_compra = (producto_ingrediente.precio_compra or producto_ingrediente.costo_fabricacion or Decimal('0')) if producto_ingrediente else Decimal('0')
        # Normalizar al precio por unidad base (ej: precio por saco → precio por kg)
        costo_unitario = _div_segura(precio_por_unidad_compra, producto_ingrediente.factor_conversion_compra if producto_ingrediente else 1)

        if producto_ingrediente and unidad_base and unidad_ingrediente:
            # Convertir la cantidad (factor) a la unidad base del producto
            if unidad_base.id == unidad_ingrediente.id:
                cantidad_proporcional = ingrediente.cantidad
            else:
                factor = _div_segura(Decimal(unidad_ingrediente.factor_conversion), unidad_base.factor_conversion)
                cantidad_proporcional = ingrediente.cantidad * factor
            cantidad_sobre_base = cantidad_proporcional / Decimal('1000') if unidad_base.simbolo == 'g' and producto_ingrediente.unidad_medida_id == unidad_base.id else cantidad_proporcional
            costo_ingrediente = costo_unitario * cantidad_sobre_base
        else:
            # Fallback: cálculo directo
            costo_ingrediente = costo_unitario * ingrediente.cantidad

        # Persistir redondeado a 2 decimales (escala de columna)
        ingrediente.costo_unitario_referencia = _a_dinero(costo_unitario)
        ingrediente.costo_total_calculado = _a_dinero(costo_ingrediente)
        costo_total += ingrediente.costo_total_calculado

    # Actualizar receta (redondeado)
    receta.costo_total_calculado = _a_dinero(costo_total)
    rendimiento = receta.rendimiento if receta.rendimiento and receta.rendimiento > 0 else Decimal('1')
    receta.costo_unitario_calculado = _a_dinero(costo_total / rendimiento)

    # Propagar al producto (sin commit; lo hace el endpoint)
    producto = db.query(Producto).filter(Producto.id == receta.producto_id).first()
    if producto:
        producto.costo_fabricacion = receta.costo_unitario_calculado

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

    # No permitir productos repetidos como ingrediente
    ids_ingredientes = [ing.producto_ingrediente_id for ing in receta_data.ingredientes]
    if len(ids_ingredientes) != len(set(ids_ingredientes)):
        raise HTTPException(status_code=400, detail="La receta tiene un producto repetido como ingrediente")

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

    # Agregar ingredientes a la relación (queda poblada en memoria para el cálculo)
    for ing_data in receta_data.ingredientes:
        db_receta.ingredientes.append(IngredienteRecetaModel(**ing_data.model_dump()))

    # Transacción única: desactivar anteriores + receta + ingredientes + costos + flag
    try:
        calcular_costos_receta(db_receta, db)
        producto.tiene_receta = True
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear la receta")

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

    try:
        calcular_costos_receta(db_receta, db)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar la receta")

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
    db.flush()

    # Verificar si quedan recetas para este producto
    tiene_recetas = db.query(RecetaModel).filter(RecetaModel.producto_id == producto_id).count() > 0

    # Actualizar flag del producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        producto.tiene_receta = tiene_recetas
        if not tiene_recetas:
            producto.costo_fabricacion = None

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar la receta")

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

    # No permitir el mismo producto dos veces en la receta
    if any(i.producto_ingrediente_id == ingrediente.producto_ingrediente_id for i in receta.ingredientes):
        raise HTTPException(status_code=400, detail="El producto ya es un ingrediente de esta receta")

    # Crear ingrediente vía la relación (poblada en memoria para el cálculo)
    db_ingrediente = IngredienteRecetaModel(**ingrediente.model_dump())
    receta.ingredientes.append(db_ingrediente)

    try:
        calcular_costos_receta(receta, db)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al agregar el ingrediente")

    db.refresh(db_ingrediente)
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

    receta = db.query(RecetaModel).filter(RecetaModel.id == db_ingrediente.receta_id).first()

    try:
        if receta:
            calcular_costos_receta(receta, db)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar el ingrediente")

    db.refresh(db_ingrediente)
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
    
    receta = db.query(RecetaModel).filter(RecetaModel.id == db_ingrediente.receta_id).first()

    # Quitar de la relación (cascade delete-orphan) para que el recálculo no lo incluya
    if receta and db_ingrediente in receta.ingredientes:
        receta.ingredientes.remove(db_ingrediente)
    else:
        db.delete(db_ingrediente)

    try:
        if receta:
            calcular_costos_receta(receta, db)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar el ingrediente")

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
    
    try:
        calcular_costos_receta(receta, db)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al recalcular costos")

    db.refresh(receta)
    return receta
