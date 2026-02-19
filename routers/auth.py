from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database.database import get_db
from database.models import User, Role, MenuItem as MenuItemModel, Tenant
from schemas.auth import Token, UserCreate, User as UserSchema, MenuItem
from utils.security import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from services import tenant_service

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
        tenant_id: int = payload.get("tenant_id")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Buscar usuario por email Y tenant_id (si está en el token)
    query = db.query(User).filter(User.email == email)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    
    user = query.first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Login inteligente que soporta:
    - Web/Backoffice: Detecta tenant por hostname (X-Forwarded-Host)
    - Apps Móviles: Busca usuario por email y usa su tenant_id
    """
    # Intentar detectar tenant desde el request (hostname)
    tenant_from_request = tenant_service.get_tenant_from_request(request, db)
    hostname = request.headers.get("x-forwarded-host", request.headers.get("host", "unknown"))
    
    # Determinar si el hostname es útil (no es IP ni localhost en fallback)
    is_hostname_useful = (
        tenant_from_request and 
        tenant_from_request.id != 1 and 
        not hostname.replace(".", "").replace(":", "").isdigit()  # No es IP
    )
    
    if is_hostname_useful:
        # Modo WEB: Hostname específico detectado (ej: elolivo.masasestacion.cl)
        # Buscar usuario por email Y tenant_id del hostname
        tenant = tenant_from_request
        tenant_service.validar_tenant_activo(tenant)
        
        user = db.query(User).filter(
            User.email == form_data.username,
            User.tenant_id == tenant.id
        ).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Modo MOBILE: Hostname es IP o localhost en fallback
        # Buscar usuario solo por email y usar su tenant_id
        user = db.query(User).filter(
            User.email == form_data.username
        ).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obtener tenant del usuario
        tenant = db.query(Tenant).filter(
            Tenant.id == user.tenant_id
        ).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant del usuario no encontrado"
            )
        
        tenant_service.validar_tenant_activo(tenant)
    
    # Generar token con tenant_id correcto
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.nombre if user.role else None, "tenant_id": tenant.id},
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
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)], db: Session = Depends(get_db)):
    """
    Obtiene información del usuario actual incluyendo datos de su tenant.
    """
    # Obtener información del tenant
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    
    # Enrichar el usuario con información del tenant
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "nombre_completo": current_user.nombre_completo,
        "is_active": current_user.is_active,
        "local_defecto_id": current_user.local_defecto_id,
        "tenant_id": current_user.tenant_id,
        "tenant_nombre": tenant.nombre if tenant else None,
        "tenant_dominio": tenant.dominio_principal if tenant else None,
        "role": current_user.role
    }
    
    return user_dict

@router.get("/menu", response_model=List[MenuItem])
def get_user_menu(current_user: User = Depends(get_current_active_user)):
    """
    Obtiene los items de menú permitidos para el rol del usuario actual.
    """
    role = current_user.role
    if not role:
        return []
    
    # Ordenar por campo 'orden'
    return sorted(role.menus, key=lambda x: x.orden)
