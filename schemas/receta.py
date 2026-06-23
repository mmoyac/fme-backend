"""
Schemas Pydantic para Recetas e Ingredientes.
"""
from pydantic import BaseModel, Field, condecimal
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

# Tipos con precisión acotada a las columnas de la BD.
# cantidad se usa como FACTOR de costeo: Numeric(18,8).
CantidadFactor = condecimal(gt=0, max_digits=18, decimal_places=8)
# rendimiento: Numeric(10,3).
Rendimiento = condecimal(gt=0, max_digits=10, decimal_places=3)


# ============================================
# INGREDIENTES DE RECETA
# ============================================

class IngredienteRecetaBase(BaseModel):
    """Schema base de Ingrediente de Receta."""
    producto_ingrediente_id: int = Field(..., description="ID del producto usado como ingrediente")
    # cantidad se usa como FACTOR de costeo: hasta 8 decimales (columna Numeric(18,8)).
    cantidad: CantidadFactor = Field(
        ..., description="Cantidad/factor del ingrediente (hasta 8 decimales)",
    )
    unidad_medida_id: int = Field(..., description="ID de la unidad de medida")
    orden: int = Field(default=0, description="Orden de visualización")
    notas: Optional[str] = None


class IngredienteRecetaCreate(IngredienteRecetaBase):
    """Schema para crear un Ingrediente de Receta."""
    pass


class IngredienteRecetaUpdate(BaseModel):
    """Schema para actualizar un Ingrediente de Receta."""
    producto_ingrediente_id: Optional[int] = None
    cantidad: Optional[CantidadFactor] = None
    unidad_medida_id: Optional[int] = None
    orden: Optional[int] = None
    notas: Optional[str] = None


class IngredienteRecetaResponse(IngredienteRecetaBase):
    """Schema de respuesta de Ingrediente de Receta."""
    id: int
    receta_id: int
    costo_unitario_referencia: Optional[Decimal] = None
    costo_total_calculado: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ============================================
# RECETAS
# ============================================

class RecetaBase(BaseModel):
    """Schema base de Receta."""
    nombre: str = Field(..., min_length=1, max_length=255)
    rendimiento: Rendimiento = Field(..., description="Cantidad que produce esta receta")
    unidad_rendimiento_id: int = Field(..., description="ID de la unidad de medida del rendimiento")
    notas: Optional[str] = None
    activa: bool = True


class RecetaCreate(RecetaBase):
    """Schema para crear una Receta."""
    ingredientes: List[IngredienteRecetaCreate] = Field(default=[], description="Lista de ingredientes")


class RecetaUpdate(BaseModel):
    """Schema para actualizar una Receta."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    rendimiento: Optional[Rendimiento] = None
    unidad_rendimiento_id: Optional[int] = None
    notas: Optional[str] = None
    activa: Optional[bool] = None


class RecetaResponse(RecetaBase):
    """Schema de respuesta de Receta."""
    id: int
    producto_id: int
    version: int
    costo_total_calculado: Optional[Decimal] = None
    costo_unitario_calculado: Optional[Decimal] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    ingredientes: List[IngredienteRecetaResponse] = []

    class Config:
        from_attributes = True


class RecetaConDetalles(RecetaResponse):
    """Schema de respuesta de Receta con información adicional."""
    producto_nombre: Optional[str] = None
    unidad_rendimiento_nombre: Optional[str] = None
    unidad_rendimiento_simbolo: Optional[str] = None
