from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database.database import get_db
from database.models import User, Role
from schemas.auth import Token, UserCreate, User as UserSchema
from utils.security import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

# Dual Support:
# 1. OAuth2PasswordBearer: For automatic Swagger UI login (User/Pass)
# 2. HTTPBearer: For manual token pasting (e.g. valid when testing existing tokens)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)
security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Session = Depends(get_db)
):
    # Determine which method provided the token
    final_token = None
    if token:
        final_token = token
    elif auth:
        final_token = auth.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not final_token:
        raise credentials_exception

    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.nombre if user.role else None},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/setup/create_admin", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_initial_admin(db: Session = Depends(get_db)):
    """
    Endpoint temporal para crear el primer usuario admin.
    Credenciales por defecto: admin@fme.cl / admin
    Solo funciona si NO existen usuarios en la base de datos.
    """
    # Verificar si ya existen usuarios
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Users already exist. Setup disabled.")
    
    # Crear Rol Admin si no existe
    admin_role = db.query(Role).filter(Role.nombre == "admin").first()
    if not admin_role:
        admin_role = Role(nombre="admin", descripcion="Administrador del sistema")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    
    # Crear Usuario
    hashed_password = get_password_hash("admin")
    db_user = User(
        email="admin@fme.cl",
        hashed_password=hashed_password,
        nombre_completo="Admin Inicial",
        role_id=admin_role.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user
