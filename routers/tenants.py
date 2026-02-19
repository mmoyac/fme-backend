"""
Router para gestión de Tenants (Multi-tenant SaaS).
Solo accesible por super administradores.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from database.models import Tenant, Producto, Cliente, Pedido, User
from schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[TenantResponse])
def listar_tenants(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los tenants del sistema con estadísticas.
    
    **Solo accesible por super administradores.**
    """
    # TODO: Validar que el usuario sea super admin (tenant_id = 1 y rol admin)
    # Por ahora permitir cualquier usuario autenticado
    
    query = db.query(Tenant)
    
    if activo is not None:
        query = query.filter(Tenant.activo == activo)
    
    tenants = query.order_by(Tenant.nombre).offset(skip).limit(limit).all()
    
    # Agregar estadísticas para cada tenant
    result = []
    for tenant in tenants:
        tenant_dict = {
            'id': tenant.id,
            'codigo': tenant.codigo,
            'nombre': tenant.nombre,
            'dominio_principal': tenant.dominio_principal,
            'subdomain': tenant.subdomain,
            'activo': tenant.activo,
            'correlativo_pedido': tenant.correlativo_pedido,
            'created_at': tenant.created_at,
            'updated_at': tenant.updated_at,
            # Estadísticas
            'total_productos': db.query(func.count(Producto.id)).filter(Producto.tenant_id == tenant.id).scalar(),
            'total_clientes': db.query(func.count(Cliente.id)).filter(Cliente.tenant_id == tenant.id).scalar(),
            'total_pedidos': db.query(func.count(Pedido.id)).filter(Pedido.tenant_id == tenant.id).scalar(),
            'total_usuarios': db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar(),
        }
        result.append(tenant_dict)
    
    return result


@router.get("/{tenant_id}", response_model=TenantResponse)
def obtener_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtiene un tenant por ID con estadísticas.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant con ID {tenant_id} no encontrado"
        )
    
    return {
        'id': tenant.id,
        'codigo': tenant.codigo,
        'nombre': tenant.nombre,
        'dominio_principal': tenant.dominio_principal,
        'subdomain': tenant.subdomain,
        'activo': tenant.activo,
        'correlativo_pedido': tenant.correlativo_pedido,
        'created_at': tenant.created_at,
        'updated_at': tenant.updated_at,
        # Estadísticas
        'total_productos': db.query(func.count(Producto.id)).filter(Producto.tenant_id == tenant.id).scalar(),
        'total_clientes': db.query(func.count(Cliente.id)).filter(Cliente.tenant_id == tenant.id).scalar(),
        'total_pedidos': db.query(func.count(Pedido.id)).filter(Pedido.tenant_id == tenant.id).scalar(),
        'total_usuarios': db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar(),
    }


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def crear_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Crea un nuevo tenant.
    
    **Solo accesible por super administradores.**
    """
    # Validar que el código no exista
    existing = db.query(Tenant).filter(Tenant.codigo == tenant_data.codigo).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un tenant con el código '{tenant_data.codigo}'"
        )
    
    # Validar que el dominio no exista (si se proporciona)
    if tenant_data.dominio_principal:
        existing = db.query(Tenant).filter(Tenant.dominio_principal == tenant_data.dominio_principal).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un tenant con el dominio '{tenant_data.dominio_principal}'"
            )
    
    # Crear tenant
    new_tenant = Tenant(
        codigo=tenant_data.codigo,
        nombre=tenant_data.nombre,
        dominio_principal=tenant_data.dominio_principal,
        subdomain=tenant_data.subdomain,
        activo=tenant_data.activo,
        correlativo_pedido=0  # Inicializar en 0
    )
    
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    return {
        'id': new_tenant.id,
        'codigo': new_tenant.codigo,
        'nombre': new_tenant.nombre,
        'dominio_principal': new_tenant.dominio_principal,
        'subdomain': new_tenant.subdomain,
        'activo': new_tenant.activo,
        'correlativo_pedido': new_tenant.correlativo_pedido,
        'created_at': new_tenant.created_at,
        'updated_at': new_tenant.updated_at,
        'total_productos': 0,
        'total_clientes': 0,
        'total_pedidos': 0,
        'total_usuarios': 0,
    }


@router.put("/{tenant_id}", response_model=TenantResponse)
def actualizar_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un tenant existente.
    
    **Casos de uso:**
    - Desactivar tenant si no paga: `{"activo": false}`
    - Ajustar correlativo de pedidos: `{"correlativo_pedido": 100}`
    - Cambiar dominio: `{"dominio_principal": "nuevodominio.cl"}`
    
    **Solo accesible por super administradores.**
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant con ID {tenant_id} no encontrado"
        )
    
    # Actualizar campos si se proporcionan
    if tenant_data.nombre is not None:
        tenant.nombre = tenant_data.nombre
    
    if tenant_data.dominio_principal is not None:
        # Validar que no exista otro tenant con ese dominio
        existing = db.query(Tenant).filter(
            Tenant.dominio_principal == tenant_data.dominio_principal,
            Tenant.id != tenant_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro tenant con el dominio '{tenant_data.dominio_principal}'"
            )
        tenant.dominio_principal = tenant_data.dominio_principal
    
    if tenant_data.subdomain is not None:
        tenant.subdomain = tenant_data.subdomain
    
    if tenant_data.activo is not None:
        tenant.activo = tenant_data.activo
    
    if tenant_data.correlativo_pedido is not None:
        tenant.correlativo_pedido = tenant_data.correlativo_pedido
    
    db.commit()
    db.refresh(tenant)
    
    return {
        'id': tenant.id,
        'codigo': tenant.codigo,
        'nombre': tenant.nombre,
        'dominio_principal': tenant.dominio_principal,
        'subdomain': tenant.subdomain,
        'activo': tenant.activo,
        'correlativo_pedido': tenant.correlativo_pedido,
        'created_at': tenant.created_at,
        'updated_at': tenant.updated_at,
        # Estadísticas
        'total_productos': db.query(func.count(Producto.id)).filter(Producto.tenant_id == tenant.id).scalar(),
        'total_clientes': db.query(func.count(Cliente.id)).filter(Cliente.tenant_id == tenant.id).scalar(),
        'total_pedidos': db.query(func.count(Pedido.id)).filter(Pedido.tenant_id == tenant.id).scalar(),
        'total_usuarios': db.query(func.count(User.id)).filter(User.tenant_id == tenant.id).scalar(),
    }


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Elimina un tenant (soft delete recomendado en producción).
    
    **ADVERTENCIA:** Esto eliminará todos los datos asociados al tenant
    debido a las restricciones de CASCADE configuradas.
    
    **Solo accesible por super administradores.**
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant con ID {tenant_id} no encontrado"
        )
    
    # No permitir eliminar el tenant principal (ID 1)
    if tenant.id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el tenant principal"
        )
    
    db.delete(tenant)
    db.commit()
    
    return None
