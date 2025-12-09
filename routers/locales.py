"""
Router para endpoints de Locales/Sucursales.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Local
from schemas.local import LocalResponse, LocalCreate, LocalUpdate

router = APIRouter()


@router.get("/", response_model=List[LocalResponse])
def listar_locales(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista todos los locales/sucursales.
    
    **Uso:** Backoffice - Tabla de locales
    """
    locales = db.query(Local).offset(skip).limit(limit).all()
    return locales


@router.get("/{local_id}", response_model=LocalResponse)
def obtener_local(local_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un local por ID.
    
    **Uso:** Backoffice - Detalle/Edición de local
    """
    local = db.query(Local).filter(Local.id == local_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    return local


@router.post("/", response_model=LocalResponse, status_code=status.HTTP_201_CREATED)
def crear_local(local: LocalCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo local/sucursal.
    
    **Validaciones:**
    - Nombre debe ser único
    - Código se genera automáticamente (formato: LOC_###)
    
    **Uso:** Backoffice - Crear local
    """
    # Verificar que el nombre no exista
    existing = db.query(Local).filter(Local.nombre == local.nombre).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un local con nombre '{local.nombre}'"
        )
    
    # Generar código automático
    max_id = db.query(Local).count()
    codigo = f"LOC_{max_id + 1:03d}"
    
    # Crear nuevo local
    db_local = Local(**local.model_dump(), codigo=codigo)
    db.add(db_local)
    db.commit()
    db.refresh(db_local)
    return db_local


@router.put("/{local_id}", response_model=LocalResponse)
def actualizar_local(
    local_id: int,
    local: LocalUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un local existente.
    
    **Validaciones:**
    - Si se cambia el nombre, debe ser único
    
    **Uso:** Backoffice - Editar local
    """
    db_local = db.query(Local).filter(Local.id == local_id).first()
    if not db_local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Si se está actualizando el nombre, verificar que sea único
    if local.nombre and local.nombre != db_local.nombre:
        existing = db.query(Local).filter(Local.nombre == local.nombre).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un local con nombre '{local.nombre}'"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = local.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_local, field, value)
    
    db.commit()
    db.refresh(db_local)
    return db_local


@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_local(local_id: int, db: Session = Depends(get_db)):
    """
    Elimina un local/sucursal.
    
    **Nota:** Esto también eliminará todos los registros relacionados:
    - Inventario del local
    - Precios del local
    
    **Uso:** Backoffice - Eliminar local
    """
    db_local = db.query(Local).filter(Local.id == local_id).first()
    if not db_local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    db.delete(db_local)
    db.commit()
    return None
