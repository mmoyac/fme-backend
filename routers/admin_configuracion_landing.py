"""
Router ADMIN para gestión de ConfiguracionLanding (White-label).
Requiere autenticación y permisos de administrador.
"""
from typing import List
import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import ConfiguracionLanding, Tenant
from schemas.configuracion_landing import (
    ConfiguracionLandingCreate,
    ConfiguracionLandingUpdate,
    ConfiguracionLandingResponse
)
from routers.auth import get_current_active_user

router = APIRouter()

# Configuración de uploads
UPLOAD_DIR = Path("static/uploads/landing")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/upload-imagen")
async def upload_imagen(
    tipo: str,  # 'logo' o 'favicon'
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Subir imagen para logo o favicon.
    Tipos permitidos: logo, favicon
    """
    # Validar tipo
    if tipo not in ['logo', 'favicon']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo debe ser 'logo' o 'favicon'"
        )
    
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión {file_ext} no permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Leer archivo y validar tamaño
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Generar nombre único
    unique_filename = f"{tipo}_{current_user.tenant_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Guardar archivo
    with open(file_path, "wb") as buffer:
        buffer.write(contents)
    
    # Retornar URL pública
    file_url = f"/static/uploads/landing/{unique_filename}"
    
    return {
        "success": True,
        "url": file_url,
        "filename": unique_filename,
        "tipo": tipo
    }


@router.get("/", response_model=List[ConfiguracionLandingResponse])
def listar_configuraciones(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Listar todas las configuraciones de landing por tenant.
    Solo admin puede ver todas, usuarios normales solo ven la de su tenant.
    """
    # Si es admin, puede ver todas
    if current_user.role and current_user.role.nombre == 'admin':
        configs = db.query(ConfiguracionLanding).all()
    else:
        # Usuario normal solo ve la de su tenant
        configs = db.query(ConfiguracionLanding).filter(
            ConfiguracionLanding.tenant_id == current_user.tenant_id
        ).all()
    
    return configs


@router.get("/{tenant_id}", response_model=ConfiguracionLandingResponse)
def obtener_configuracion(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtener configuración de landing por tenant_id.
    """
    # Validar permisos: admin puede ver todas, usuario normal solo la suya
    if (not current_user.role or current_user.role.nombre != 'admin') and tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta configuración"
        )
    
    config = db.query(ConfiguracionLanding).filter(
        ConfiguracionLanding.tenant_id == tenant_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe configuración para tenant {tenant_id}"
        )
    
    return config


@router.post("/", response_model=ConfiguracionLandingResponse, status_code=status.HTTP_201_CREATED)
def crear_configuracion(
    config_data: ConfiguracionLandingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Crear nueva configuración de landing para un tenant.
    Solo admin puede crear.
    """
    # Solo admin puede crear
    if not current_user.role or current_user.role.nombre != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear configuraciones"
        )
    
    # Validar que existe el tenant
    tenant = db.query(Tenant).filter(Tenant.id == config_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {config_data.tenant_id} no encontrado"
        )
    
    # Validar que no exista configuración previa
    existing = db.query(ConfiguracionLanding).filter(
        ConfiguracionLanding.tenant_id == config_data.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe configuración para tenant {config_data.tenant_id}"
        )
    
    # Crear configuración
    db_config = ConfiguracionLanding(**config_data.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.put("/{tenant_id}", response_model=ConfiguracionLandingResponse)
def actualizar_configuracion(
    tenant_id: int,
    config_data: ConfiguracionLandingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualizar configuración de landing de un tenant.
    Admin puede actualizar todas, usuario normal solo la de su tenant.
    """
    # Validar permisos
    if (not current_user.role or current_user.role.nombre != 'admin') and tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta configuración"
        )
    
    # Buscar configuración
    db_config = db.query(ConfiguracionLanding).filter(
        ConfiguracionLanding.tenant_id == tenant_id
    ).first()
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe configuración para tenant {tenant_id}"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_configuracion(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Eliminar configuración de landing de un tenant.
    Solo admin puede eliminar.
    """
    # Solo admin puede eliminar
    if not current_user.role or current_user.role.nombre != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar configuraciones"
        )
    
    db_config = db.query(ConfiguracionLanding).filter(
        ConfiguracionLanding.tenant_id == tenant_id
    ).first()
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe configuración para tenant {tenant_id}"
        )
    
    db.delete(db_config)
    db.commit()
    
    return None
