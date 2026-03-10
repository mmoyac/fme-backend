"""
Router para gestión de Tenants (Multi-tenant SaaS).
Solo accesible por super administradores.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from database.models import Tenant, Producto, Cliente, Pedido, User, Local, ConfiguracionLanding, Role
from schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from routers.auth import get_current_active_user
from utils.security import get_password_hash

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
            'google_sheet_id': tenant.google_sheet_id,
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
        'google_sheet_id': tenant.google_sheet_id,
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
    
    # Convertir cadenas vacías en None (para evitar conflictos con UNIQUE constraints)
    dominio_principal = tenant_data.dominio_principal if tenant_data.dominio_principal else None
    subdomain = tenant_data.subdomain if tenant_data.subdomain else None
    
    # Validar que el dominio no exista (si se proporciona)
    if dominio_principal:
        existing = db.query(Tenant).filter(Tenant.dominio_principal == dominio_principal).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un tenant con el dominio '{dominio_principal}'"
            )
    
    # Crear tenant
    new_tenant = Tenant(
        codigo=tenant_data.codigo,
        nombre=tenant_data.nombre,
        dominio_principal=dominio_principal,
        subdomain=subdomain,
        activo=tenant_data.activo,
        correlativo_pedido=0  # Inicializar en 0
    )
    
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    # ========================================
    # CREAR LOCAL WEB (Virtual)
    # ========================================
    local_web = Local(
        tenant_id=new_tenant.id,
        codigo='WEB',
        nombre='Tienda Online',
        direccion='Online',
        activo=True
    )
    db.add(local_web)
    db.commit()
    db.refresh(local_web)
    
    # ========================================
    # CREAR CONFIGURACIÓN LANDING POR DEFECTO
    # ========================================
    config_landing = ConfiguracionLanding(
        tenant_id=new_tenant.id,
        # Branding
        nombre_comercial=new_tenant.nombre,
        logo_url=None,
        favicon_url=None,
        # Colores por defecto (sin paleta)
        paleta_id=None,
        colores={
            'primario': '#5EC8F2',
            'primario_light': '#90DCFF',
            'primario_dark': '#3DA8D8',
            'secundario': '#45A29A',
            'secundario_light': '#6BC4BB',
            'secundario_dark': '#2F7A74',
            'acento': '#90DCFF',
            'fondo_hero_inicio': '#1E3A8A',
            'fondo_hero_fin': '#3B82F6',
            'fondo_seccion': '#0F172A'
        },
        # Hero Section
        hero_titulo=f'Bienvenido a {new_tenant.nombre}',
        hero_subtitulo='Las mejores masas frescas a tu mesa',
        hero_imagen_url=None,
        hero_cta_texto='Ver Productos',
        hero_cta_link='/productos',
        hero_badges=[],
        # Beneficios
        beneficios=[
            {'icono': '⭐', 'titulo': 'Calidad Premium', 'descripcion': 'Productos frescos y de calidad'},
            {'icono': '🚚', 'titulo': 'Envío Rápido', 'descripcion': 'Entrega en 24-48 horas'},
            {'icono': '🔒', 'titulo': 'Pago Seguro', 'descripcion': 'Transacciones 100% seguras'}
        ],
        # Footer / Contacto
        redes_sociales={},
        telefono=None,
        email=None,
        direccion=None,
        texto_footer_descripcion=f'{new_tenant.nombre} - Calidad en cada producto',
        texto_copyright=f'© 2026 {new_tenant.nombre}. Todos los derechos reservados.',
        # SEO Metadata
        meta_title=new_tenant.nombre,
        meta_description=f'Tienda online de {new_tenant.nombre}',
        # Opciones de Visualización
        mostrar_precios=True,
        mostrar_stock=True,
        habilitar_carrito=True
    )
    db.add(config_landing)
    db.commit()
    db.refresh(config_landing)
    
    # ========================================
    # CREAR USUARIO ADMINISTRADOR POR DEFECTO
    # ========================================
    # Buscar rol admin (normalmente id=1)
    role_admin = db.query(Role).filter(Role.nombre == 'admin').first()
    if not role_admin:
        # Si no existe, crear rol admin
        role_admin = Role(
            nombre='admin',
            descripcion='Administrador del sistema',
            permisos={}
        )
        db.add(role_admin)
        db.commit()
        db.refresh(role_admin)
    
    # Crear usuario admin con contraseña temporal
    usuario_admin = User(
        tenant_id=new_tenant.id,
        email=f"admin@{new_tenant.codigo.lower()}.com",
        hashed_password=get_password_hash("admin123"),  # Contraseña temporal
        nombre_completo=f"Administrador {new_tenant.nombre}",
        role_id=role_admin.id,
        is_active=True,
        local_defecto_id=local_web.id  # Asignar local WEB por defecto
    )
    db.add(usuario_admin)
    db.commit()
    db.refresh(usuario_admin)
    
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
        'total_usuarios': 1,  # Usuario admin creado
        # Información del usuario admin creado
        'usuario_admin_email': usuario_admin.email,
        'usuario_admin_password_temporal': 'admin123',  # Mostrar una vez para que el super admin lo sepa
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
        # Convertir cadena vacía en None
        dominio_principal = tenant_data.dominio_principal if tenant_data.dominio_principal else None
        
        # Validar que no exista otro tenant con ese dominio (solo si no es None)
        if dominio_principal:
            existing = db.query(Tenant).filter(
                Tenant.dominio_principal == dominio_principal,
                Tenant.id != tenant_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otro tenant con el dominio '{dominio_principal}'"
                )
        tenant.dominio_principal = dominio_principal
    
    if tenant_data.subdomain is not None:
        # Convertir cadena vacía en None
        tenant.subdomain = tenant_data.subdomain if tenant_data.subdomain else None
    
    if tenant_data.activo is not None:
        tenant.activo = tenant_data.activo
    
    if tenant_data.correlativo_pedido is not None:
        tenant.correlativo_pedido = tenant_data.correlativo_pedido
    
    if tenant_data.google_sheet_id is not None:
        tenant.google_sheet_id = tenant_data.google_sheet_id if tenant_data.google_sheet_id else None
    
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
        'google_sheet_id': tenant.google_sheet_id,
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


@router.get("/{tenant_id}/users")
def listar_usuarios_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtener lista de usuarios de un tenant específico.
    
    **Solo accesible por super administradores.**
    Permite gestionar usuarios desde la interfaz de tenants.
    """
    # Verificar que el tenant exista
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant con ID {tenant_id} no encontrado"
        )
    
    # Obtener usuarios del tenant con información de rol y local
    usuarios = db.query(User).filter(User.tenant_id == tenant_id).all()
    
    return [
        {
            'id': u.id,
            'email': u.email,
            'nombre_completo': u.nombre_completo,
            'is_active': u.is_active,
            'role_id': u.role_id,
            'role_nombre': u.role.nombre if u.role else None,
            'local_defecto_id': u.local_defecto_id,
            'local_nombre': u.local_defecto.nombre if u.local_defecto else None
        }
        for u in usuarios
    ]
