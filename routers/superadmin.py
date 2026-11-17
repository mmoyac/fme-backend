"""
Router de Super Administrador de Plataforma.
Solo accesible por usuarios con is_superadmin=True.
Permite gestión cross-tenant y generación de tokens de contexto.
"""
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from database.models import User, Tenant, Producto, Cliente, Pedido, Role, TenantModulo
from utils.modulos import MODULOS, REQUIERE, modulos_de_tenant, validar_cambio
from schemas.tenant import TenantResponse, TenantCreate, TenantUpdate
from routers.auth import get_current_superadmin
from utils.security import create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


# --------------------------------------------------
# Schemas locales
# --------------------------------------------------

class TenantWithStats(BaseModel):
    id: int
    codigo: str
    nombre: str
    dominio_principal: Optional[str] = None
    subdomain: Optional[str] = None
    activo: bool
    correlativo_pedido: int
    total_usuarios: int
    total_productos: int
    total_clientes: int
    total_pedidos: int

    class Config:
        from_attributes = True


class SwitchTenantResponse(BaseModel):
    access_token: str
    token_type: str
    tenant_id: int
    tenant_nombre: str


class CreateSuperAdminRequest(BaseModel):
    email: str
    password: str
    nombre_completo: str


# --------------------------------------------------
# Endpoints
# --------------------------------------------------

@router.get("/tenants", response_model=List[TenantWithStats])
def listar_todos_los_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """Lista todos los tenants con estadísticas de uso."""
    tenants = db.query(Tenant).order_by(Tenant.nombre).all()
    result = []
    for t in tenants:
        result.append(TenantWithStats(
            id=t.id,
            codigo=t.codigo,
            nombre=t.nombre,
            dominio_principal=t.dominio_principal,
            subdomain=t.subdomain,
            activo=t.activo,
            correlativo_pedido=t.correlativo_pedido,
            total_usuarios=db.query(func.count(User.id)).filter(User.tenant_id == t.id).scalar() or 0,
            total_productos=db.query(func.count(Producto.id)).filter(Producto.tenant_id == t.id).scalar() or 0,
            total_clientes=db.query(func.count(Cliente.id)).filter(Cliente.tenant_id == t.id).scalar() or 0,
            total_pedidos=db.query(func.count(Pedido.id)).filter(Pedido.tenant_id == t.id).scalar() or 0,
        ))
    return result


@router.post("/switch-tenant/{tenant_id}", response_model=SwitchTenantResponse)
def switch_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Genera un token de contexto que permite al superadmin operar dentro de un tenant específico.
    El token lleva is_superadmin=True + tenant_id, lo que hace que get_current_user
    inyecte el tenant_id en el objeto user sin cambiar quién es el usuario.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    access_token = create_access_token(
        data={
            "sub": current_user.email,
            "is_superadmin": True,
            "tenant_id": tenant_id,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return SwitchTenantResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_id=tenant_id,
        tenant_nombre=tenant.nombre
    )


@router.post("/exit-tenant", response_model=dict)
def exit_tenant(
    current_user: User = Depends(get_current_superadmin)
):
    """
    Genera un token limpio de superadmin sin tenant_id (vuelve al modo plataforma).
    """
    access_token = create_access_token(
        data={"sub": current_user.email, "is_superadmin": True},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/stats")
def estadisticas_plataforma(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """Estadísticas globales de la plataforma."""
    return {
        "total_tenants": db.query(func.count(Tenant.id)).scalar() or 0,
        "tenants_activos": db.query(func.count(Tenant.id)).filter(Tenant.activo == True).scalar() or 0,
        "total_usuarios": db.query(func.count(User.id)).filter(User.is_superadmin == False).scalar() or 0,
        "total_pedidos": db.query(func.count(Pedido.id)).scalar() or 0,
        "total_clientes": db.query(func.count(Cliente.id)).scalar() or 0,
    }


class ModuloCatalogo(BaseModel):
    codigo: str
    nombre: str
    requiere: List[str]


class ModulosTenantRequest(BaseModel):
    modulos: List[str]


class ModulosTenantResponse(BaseModel):
    tenant_id: int
    modulos: List[str]


@router.get("/modulos", response_model=List[ModuloCatalogo])
def catalogo_modulos(current_user: User = Depends(get_current_superadmin)):
    """Catálogo de módulos contratables (el núcleo siempre está incluido y no figura)."""
    return [
        ModuloCatalogo(codigo=c, nombre=n, requiere=sorted(REQUIERE.get(c, frozenset())))
        for c, n in MODULOS.items()
    ]


@router.get("/tenants/{tenant_id}/modulos", response_model=ModulosTenantResponse)
def obtener_modulos_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return ModulosTenantResponse(tenant_id=tenant_id, modulos=sorted(modulos_de_tenant(db, tenant_id)))


@router.put("/tenants/{tenant_id}/modulos", response_model=ModulosTenantResponse)
def actualizar_modulos_tenant(
    tenant_id: int,
    body: ModulosTenantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """Reemplaza el conjunto de módulos contratados (idempotente). Valida dependencias."""
    if not db.query(Tenant.id).filter(Tenant.id == tenant_id).first():
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    actuales = modulos_de_tenant(db, tenant_id)
    nuevos = set(body.modulos)
    error = validar_cambio(actuales, nuevos)
    if error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error)

    quitar = actuales - nuevos
    if quitar:
        db.query(TenantModulo).filter(
            TenantModulo.tenant_id == tenant_id, TenantModulo.modulo.in_(quitar)
        ).delete(synchronize_session=False)
    for modulo in sorted(nuevos - actuales):
        db.add(TenantModulo(tenant_id=tenant_id, modulo=modulo, activado_por=current_user.email))
    # TODO(harden-platform-admin fase 2): registrar en la bitácora (agregados/quitados, actor)
    db.commit()
    return ModulosTenantResponse(tenant_id=tenant_id, modulos=sorted(nuevos))


@router.put("/tenants/{tenant_id}/toggle-activo")
def toggle_tenant_activo(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """Activa o desactiva un tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    tenant.activo = not tenant.activo
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "nombre": tenant.nombre, "activo": tenant.activo}


@router.post("/create-superadmin", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_superadmin(
    data: CreateSuperAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """Crea otro usuario superadmin. Solo accesible por un superadmin existente."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está en uso")

    # El superadmin vive en el tenant 1 (tenant raíz de la plataforma)
    tenant_raiz = db.query(Tenant).order_by(Tenant.id).first()
    if not tenant_raiz:
        raise HTTPException(status_code=400, detail="No existe ningún tenant en el sistema")

    # Obtener o crear rol 'superadmin' en tenant 1
    role = db.query(Role).filter(
        Role.nombre == "superadmin",
        Role.tenant_id == tenant_raiz.id
    ).first()
    if not role:
        role = Role(nombre="superadmin", descripcion="Super administrador de plataforma", tenant_id=tenant_raiz.id)
        db.add(role)
        db.commit()
        db.refresh(role)

    new_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        nombre_completo=data.nombre_completo,
        is_active=True,
        is_superadmin=True,
        role_id=role.id,
        tenant_id=tenant_raiz.id,
    )
    db.add(new_user)
    db.commit()
    return {"id": new_user.id, "email": new_user.email, "nombre_completo": new_user.nombre_completo}
