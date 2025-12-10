"""
Router para gestión de usuarios y roles (Backoffice Admin).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Annotated

from database.database import get_db
from database.models import User, Role, MenuItem as MenuItemModel
from schemas.auth import User as UserSchema, UserCreate, Role as RoleSchema, RoleCreate, MenuItem as MenuItemSchema, MenuItemCreate
from routers.auth import get_current_active_user
from utils.security import get_password_hash

router = APIRouter()

# ... (Dependencies and User CRUD remain the same) ...
# Dependencia para verificar que el usuario es admin
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    allowed_roles = ["admin", "owner", "administrador"]
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user

# --------------------------------------------------
# Gestión de Roles y Permisos (Menú)
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

@router.get("/menu_items", response_model=List[MenuItemSchema])
def listar_items_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Listar todos los items de menú disponibles en el sistema."""
    return db.query(MenuItemModel).order_by(MenuItemModel.orden).all()

@router.post("/menu_items", response_model=MenuItemSchema, status_code=status.HTTP_201_CREATED)
def crear_item_menu(
    menu_item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo item de menú."""
    db_menu_item = MenuItemModel(
        nombre=menu_item.nombre,
        href=menu_item.href,
        icon=menu_item.icon,
        orden=menu_item.orden
    )
    db.add(db_menu_item)
    db.commit()
    db.refresh(db_menu_item)
    return db_menu_item

@router.put("/menu_items/{menu_item_id}", response_model=MenuItemSchema)
def actualizar_item_menu(
    menu_item_id: int,
    menu_item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un item de menú existente."""
    db_menu_item = db.query(MenuItemModel).filter(MenuItemModel.id == menu_item_id).first()
    if not db_menu_item:
        raise HTTPException(status_code=404, detail="Menu item no encontrado")
    
    db_menu_item.nombre = menu_item.nombre
    db_menu_item.href = menu_item.href
    db_menu_item.icon = menu_item.icon
    db_menu_item.orden = menu_item.orden
    
    db.commit()
    db.refresh(db_menu_item)
    return db_menu_item

@router.get("/roles/{role_id}/menu", response_model=List[MenuItemSchema])
def obtener_menu_rol(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obtener items asignados a un rol."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role.menus

@router.put("/roles/{role_id}/menu", status_code=status.HTTP_204_NO_CONTENT)
def actualizar_menu_rol(
    role_id: int,
    menu_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar permisos de menú para un rol."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Obtener items correspondientes a los IDs
    items = db.query(MenuItemModel).filter(MenuItemModel.id.in_(menu_ids)).all()
    
    # Actualizar relación
    role.menus = items
    db.commit()
    return None

# --------------------------------------------------
# Gestión de Usuarios (Resto igual)
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
