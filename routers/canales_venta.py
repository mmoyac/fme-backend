"""
Router para gestión de canales de venta (POS, LANDING, WHATSAPP, etc.)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from database.models import CanalVenta
from routers.auth import get_current_active_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────

class CanalVentaResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    activo: bool

    class Config:
        from_attributes = True


class CanalVentaCreate(BaseModel):
    codigo: str
    nombre: str
    activo: bool = True


class CanalVentaUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/", response_model=List[CanalVentaResponse])
def listar_canales_venta(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return db.query(CanalVenta).order_by(CanalVenta.id).all()


@router.post("/", response_model=CanalVentaResponse, status_code=status.HTTP_201_CREATED)
def crear_canal_venta(
    data: CanalVentaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if db.query(CanalVenta).filter(CanalVenta.codigo == data.codigo.upper()).first():
        raise HTTPException(status_code=400, detail=f"Ya existe un canal con código '{data.codigo}'")
    canal = CanalVenta(codigo=data.codigo.upper(), nombre=data.nombre, activo=data.activo)
    db.add(canal)
    db.commit()
    db.refresh(canal)
    return canal


@router.put("/{canal_id}", response_model=CanalVentaResponse)
def actualizar_canal_venta(
    canal_id: int,
    data: CanalVentaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    canal = db.query(CanalVenta).filter(CanalVenta.id == canal_id).first()
    if not canal:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    if data.nombre is not None:
        canal.nombre = data.nombre
    if data.activo is not None:
        canal.activo = data.activo
    db.commit()
    db.refresh(canal)
    return canal


@router.delete("/{canal_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_canal_venta(
    canal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    canal = db.query(CanalVenta).filter(CanalVenta.id == canal_id).first()
    if not canal:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    # Verificar que no tenga pedidos asociados
    from database.models import Pedido
    if db.query(Pedido).filter(Pedido.canal_venta_id == canal_id).first():
        raise HTTPException(status_code=400, detail="No se puede eliminar: hay pedidos asociados a este canal")
    db.delete(canal)
    db.commit()
