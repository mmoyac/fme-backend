"""
Router para gestión de usuarios y roles (Backoffice Admin).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from database.database import get_db
from database.models import User, Role
from schemas.auth import User as UserSchema, UserCreate, Role as RoleSchema, RoleCreate
from routers.auth import get_current_active_user
from utils.security import get_password_hash

router = APIRouter()

# Dependencia para verificar que el usuario es admin
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role.nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user

# --------------------------------------------------
# Gestión de Roles
# --------------------------------------------------

@router.get("/roles", response_model=List[RoleSchema])
def listar_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar todos los roles disponibles."""
    return db.query(Role).all()

@router.post("/roles", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
def crear_rol(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo rol."""
    existing = db.query(Role).filter(Role.nombre == role.nombre).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El rol '{role.nombre}' ya existe")
    
    db_role = Role(nombre=role.nombre, descripcion=role.descripcion)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# --------------------------------------------------
# Gestión de Usuarios
# --------------------------------------------------

@router.get("/users", response_model=List[UserSchema])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar usuarios del sistema."""
    return db.query(User).offset(skip).limit(limit).all()

@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo usuario y asignarle un rol."""
    # Verificar email único
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Verificar que el rol exista
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="El Rol ID especificado no existe")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        nombre_completo=user.nombre_completo,
        is_active=user.is_active,
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un usuario."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    return None
