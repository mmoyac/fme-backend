from pydantic import BaseModel
from typing import Optional

class RoleBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    nombre_completo: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str
    role_id: int

class User(UserBase):
    id: int
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
