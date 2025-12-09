"""
Router para endpoints de Productos y Catálogo.
"""
from typing import List
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Producto
from schemas.catalogo import ProductoCatalogo
from schemas.producto import ProductoResponse, ProductoCreate, ProductoUpdate
from services import inventario_service

from routers.auth import get_current_active_user

router = APIRouter()

# Directorio para guardar imágenes
UPLOAD_DIR = Path("static/productos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/catalogo", response_model=List[ProductoCatalogo])
def obtener_catalogo_web(db: Session = Depends(get_db)):
    """
    Obtiene el catálogo de productos con precios del local WEB.
    
    Retorna:
    - SKU del producto
    - Nombre del producto
    - Descripción del producto
    - Precio (del local WEB/e-commerce)
    - Stock total (suma de todos los locales físicos)
    
    **Ideal para:** Mostrar productos en la tienda online con precios de e-commerce
    """
    catalogo = inventario_service.get_catalogo_web(db)
    return catalogo


# --------------------------------------------------
# CRUD Endpoints para Backoffice
# --------------------------------------------------

@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los productos con paginación.
    
    **Uso:** Backoffice - Tabla de productos
    """
    productos = db.query(Producto).offset(skip).limit(limit).all()
    return productos


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Obtiene un producto por ID.
    
    **Uso:** Backoffice - Detalle/Edición de producto
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    return producto


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Crea un nuevo producto.
    
    **Validaciones:**
    - SKU debe ser único
    
    **Uso:** Backoffice - Crear producto
    """
    # Verificar que el SKU no exista
    existing = db.query(Producto).filter(Producto.sku == producto.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un producto con SKU '{producto.sku}'"
        )
    
    # Crear nuevo producto
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un producto existente.
    
    **Validaciones:**
    - Si se cambia el SKU, debe ser único
    
    **Uso:** Backoffice - Editar producto
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Si se está actualizando el SKU, verificar que sea único
    if producto.sku and producto.sku != db_producto.sku:
        existing = db.query(Producto).filter(Producto.sku == producto.sku).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con SKU '{producto.sku}'"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = producto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_producto, field, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Elimina un producto.
    
    **Nota:** Esto también eliminará todos los registros relacionados:
    - Inventario del producto en todos los locales
    - Precios del producto en todos los locales
    
    **Uso:** Backoffice - Eliminar producto
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    db.delete(db_producto)
    db.commit()
    return None


@router.post("/{producto_id}/imagen", response_model=ProductoResponse)
async def subir_imagen_producto(
    producto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Sube una imagen para un producto.
    
    **Formatos permitidos:** JPG, JPEG, PNG, WEBP
    **Tamaño máximo:** 2MB
    
    **Uso:** Backoffice - Upload de imagen
    """
    # Verificar que el producto existe
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Validar formato de archivo
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Use: {', '.join(allowed_extensions)}"
        )
    
    # Validar tamaño (2MB)
    max_size = 2 * 1024 * 1024  # 2MB en bytes
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo excede el tamaño máximo de 2MB"
        )
    
    # Generar nombre de archivo único usando SKU
    filename = f"{db_producto.sku}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Guardar archivo
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Actualizar URL de imagen en base de datos
    db_producto.imagen_url = f"/static/productos/{filename}"
    db.commit()
    db.refresh(db_producto)
    
    return db_producto
