from pydantic import BaseModel
from typing import Optional

class RoleBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    nombre_completo: Optional[str] = None
    is_active: Optional[bool] = True
    local_defecto_id: Optional[int] = None
    porcentaje_comision: Optional[float] = None

class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    is_active: Optional[bool] = None
    local_defecto_id: Optional[int] = None
    role_id: Optional[int] = None
    porcentaje_comision: Optional[float] = None  # None = no cambia; 0 = quitar comisión

class User(UserBase):
    id: int
    tenant_id: int
    tenant_nombre: Optional[str] = None
    tenant_dominio: Optional[str] = None
    is_superadmin: bool = False
    role: Role

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class MenuItemBase(BaseModel):
    nombre: str
    href: str
    icon: Optional[str] = None
    orden: int = 0

class MenuItemCreate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    id: int

    class Config:
        from_attributes = True
