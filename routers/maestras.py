"""
Router para gestión de tablas maestras (Categorías, Tipos, Unidades de Medida).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import CategoriaProducto as CategoriaProductoModel
from database.models import TipoProducto as TipoProductoModel
from database.models import TipoDocumento as TipoDocumentoModel
from database.models import UnidadMedida as UnidadMedidaModel
from database.models import User
from schemas.maestras import (
    CategoriaProducto, CategoriaProductoCreate, CategoriaProductoUpdate,
    TipoProducto, TipoProductoCreate, TipoProductoUpdate,
    TipoDocumento, TipoDocumentoCreate, TipoDocumentoUpdate,
    UnidadMedida, UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaConBase
)
from routers.auth import get_current_active_user

router = APIRouter()


# Dependencia para verificar que el usuario es admin
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role.nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user


# ============================================
# CATEGORÍAS DE PRODUCTO
# ============================================

@router.get("/categorias", response_model=List[CategoriaProducto])
def listar_categorias(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar categorías de productos."""
    query = db.query(CategoriaProductoModel)
    
    if activo is not None:
        query = query.filter(CategoriaProductoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/categorias/{categoria_id}", response_model=CategoriaProducto)
def obtener_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener una categoría por ID."""
    categoria = db.query(CategoriaProductoModel).filter(CategoriaProductoModel.id == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post("/categorias", response_model=CategoriaProducto, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria: CategoriaProductoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear una nueva categoría de producto."""
    # Verificar código único
    existing = db.query(CategoriaProductoModel).filter(CategoriaProductoModel.codigo == categoria.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{categoria.codigo}' ya existe")
    
    db_categoria = CategoriaProductoModel(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.put("/categorias/{categoria_id}", response_model=CategoriaProducto)
def actualizar_categoria(
    categoria_id: int,
    categoria: CategoriaProductoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar una categoría existente."""
    db_categoria = db.query(CategoriaProductoModel).filter(CategoriaProductoModel.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar código único si se está actualizando
    if categoria.codigo and categoria.codigo != db_categoria.codigo:
        existing = db.query(CategoriaProductoModel).filter(CategoriaProductoModel.codigo == categoria.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{categoria.codigo}' ya existe")
    
    update_data = categoria.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_categoria, field, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar una categoría (solo si no tiene productos asociados)."""
    db_categoria = db.query(CategoriaProductoModel).filter(CategoriaProductoModel.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si tiene productos asociados
    if db_categoria.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría porque tiene {len(db_categoria.productos)} productos asociados"
        )
    
    db.delete(db_categoria)
    db.commit()
    return None


# ============================================
# TIPOS DE PRODUCTO
# ============================================

@router.get("/tipos", response_model=List[TipoProducto])
def listar_tipos(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de productos."""
    query = db.query(TipoProductoModel)
    
    if activo is not None:
        query = query.filter(TipoProductoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/tipos/{tipo_id}", response_model=TipoProducto)
def obtener_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un tipo de producto por ID."""
    tipo = db.query(TipoProductoModel).filter(TipoProductoModel.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    return tipo


@router.post("/tipos", response_model=TipoProducto, status_code=status.HTTP_201_CREATED)
def crear_tipo(
    tipo: TipoProductoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de producto."""
    # Verificar código único
    existing = db.query(TipoProductoModel).filter(TipoProductoModel.codigo == tipo.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    db_tipo = TipoProductoModel(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.put("/tipos/{tipo_id}", response_model=TipoProducto)
def actualizar_tipo(
    tipo_id: int,
    tipo: TipoProductoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de producto existente."""
    db_tipo = db.query(TipoProductoModel).filter(TipoProductoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    
    # Verificar código único si se está actualizando
    if tipo.codigo and tipo.codigo != db_tipo.codigo:
        existing = db.query(TipoProductoModel).filter(TipoProductoModel.codigo == tipo.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    update_data = tipo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo, field, value)
    
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.delete("/tipos/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de producto (solo si no tiene productos asociados)."""
    db_tipo = db.query(TipoProductoModel).filter(TipoProductoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    
    # Verificar si tiene productos asociados
    if db_tipo.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo porque tiene {len(db_tipo.productos)} productos asociados"
        )
    
    db.delete(db_tipo)
    db.commit()
    return None

# ============================================
# TIPOS DE DOCUMENTO
# ============================================

@router.get("/tipos-documento", response_model=List[TipoDocumento])
def listar_tipos_documento(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de documento tributario."""
    query = db.query(TipoDocumentoModel)
    
    if activo is not None:
        query = query.filter(TipoDocumentoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/tipos-documento/{tipo_id}", response_model=TipoDocumento)
def obtener_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un tipo de documento por ID."""
    tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    return tipo


@router.post("/tipos-documento", response_model=TipoDocumento, status_code=status.HTTP_201_CREATED)
def crear_tipo_documento(
    tipo: TipoDocumentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de documento."""
    # Verificar código único
    existing = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.codigo == tipo.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    db_tipo = TipoDocumentoModel(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.put("/tipos-documento/{tipo_id}", response_model=TipoDocumento)
def actualizar_tipo_documento(
    tipo_id: int,
    tipo: TipoDocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de documento existente."""
    db_tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    
    # Verificar código único si se está actualizando
    if tipo.codigo and tipo.codigo != db_tipo.codigo:
        existing = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.codigo == tipo.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    update_data = tipo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo, field, value)
    
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.delete("/tipos-documento/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de documento (solo si no tiene compras asociadas)."""
    db_tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    
    # Verificar si tiene compras asociadas
    if db_tipo.compras:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo porque tiene {len(db_tipo.compras)} compras asociadas"
        )
    
    db.delete(db_tipo)
    db.commit()
    return None


# ============================================
# UNIDADES DE MEDIDA
# ============================================

@router.get("/unidades", response_model=List[UnidadMedidaConBase])
def listar_unidades(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar unidades de medida."""
    query = db.query(UnidadMedidaModel)
    
    if activo is not None:
        query = query.filter(UnidadMedidaModel.activo == activo)
    
    if tipo:
        query = query.filter(UnidadMedidaModel.tipo == tipo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/unidades/{unidad_id}", response_model=UnidadMedidaConBase)
def obtener_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener una unidad de medida por ID."""
    unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    return unidad


@router.post("/unidades", response_model=UnidadMedida, status_code=status.HTTP_201_CREATED)
def crear_unidad(
    unidad: UnidadMedidaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear una nueva unidad de medida."""
    # Verificar código único
    existing = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.codigo == unidad.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{unidad.codigo}' ya existe")
    
    # Verificar que la unidad base existe si se especifica
    if unidad.unidad_base_id:
        unidad_base = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad.unidad_base_id).first()
        if not unidad_base:
            raise HTTPException(status_code=400, detail="La unidad base especificada no existe")
    
    db_unidad = UnidadMedidaModel(**unidad.model_dump())
    db.add(db_unidad)
    db.commit()
    db.refresh(db_unidad)
    return db_unidad


@router.put("/unidades/{unidad_id}", response_model=UnidadMedida)
def actualizar_unidad(
    unidad_id: int,
    unidad: UnidadMedidaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar una unidad de medida existente."""
    db_unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    
    # Verificar código único si se está actualizando
    if unidad.codigo and unidad.codigo != db_unidad.codigo:
        existing = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.codigo == unidad.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{unidad.codigo}' ya existe")
    
    # Verificar que la unidad base existe si se especifica
    if unidad.unidad_base_id:
        unidad_base = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad.unidad_base_id).first()
        if not unidad_base:
            raise HTTPException(status_code=400, detail="La unidad base especificada no existe")
    
    update_data = unidad.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_unidad, field, value)
    
    db.commit()
    db.refresh(db_unidad)
    return db_unidad


@router.delete("/unidades/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar una unidad de medida (solo si no tiene productos asociados)."""
    db_unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    
    # Verificar si tiene productos asociados
    if db_unidad.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la unidad porque tiene {len(db_unidad.productos)} productos asociados"
        )
    
    db.delete(db_unidad)
    db.commit()
    return None
