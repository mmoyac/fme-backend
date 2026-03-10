"""
Schemas para gestión de Tenants (Multi-tenant SaaS).
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    """Schema base de Tenant."""
    nombre: str = Field(..., min_length=1, max_length=100)
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del tenant (ej: 'masas-estacion')")
    dominio_principal: Optional[str] = Field(None, max_length=100, description="Dominio principal (ej: 'masasestacion.cl')")
    subdomain: Optional[str] = Field(None, max_length=50, description="Subdominio (ej: 'masasestacion' para *.tuapp.cl)")
    activo: bool = Field(True, description="Si el tenant está activo (puede acceder al sistema)")
    google_sheet_id: Optional[str] = Field(None, max_length=200, description="ID del Google Sheet para importación de datos (ej: '1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM')")


class TenantCreate(TenantBase):
    """Schema para crear un Tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema para actualizar un Tenant."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    dominio_principal: Optional[str] = Field(None, max_length=100)
    subdomain: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = Field(None, description="Activar/desactivar tenant")
    correlativo_pedido: Optional[int] = Field(None, ge=0, description="Ajustar correlativo de pedidos")
    google_sheet_id: Optional[str] = Field(None, max_length=200, description="ID del Google Sheet para importación de datos")


class TenantResponse(TenantBase):
    """Schema de respuesta de Tenant."""
    id: int
    correlativo_pedido: int
    google_sheet_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Estadísticas
    total_productos: Optional[int] = None
    total_clientes: Optional[int] = None
    total_pedidos: Optional[int] = None
    total_usuarios: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
