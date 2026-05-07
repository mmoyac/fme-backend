"""
Router para gestión de Vehículos de despacho.
Permite CRUD de vehículos y consulta de tipos de vehículo.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel

from database.database import get_db
from database.models import Vehiculo, TipoVehiculo, User, Role
from routers.auth import get_current_active_user

router = APIRouter(prefix="/api/vehiculos", tags=["Vehículos"])


# ──────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────

class VehiculoCreate(BaseModel):
    patente: str
    capacidad_kg: float
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    tipo_vehiculo_id: Optional[int] = None


class VehiculoUpdate(BaseModel):
    patente: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    capacidad_kg: Optional[float] = None
    tipo_vehiculo_id: Optional[int] = None
    activo: Optional[bool] = None


# ──────────────────────────────────────────
# Helper
# ──────────────────────────────────────────

def _vehiculo_out(v: Vehiculo) -> dict:
    return {
        "id": v.id,
        "patente": v.patente,
        "marca": v.marca,
        "modelo": v.modelo,
        "anio": v.anio,
        "capacidad_kg": float(v.capacidad_kg) if v.capacidad_kg else None,
        "activo": v.activo,
        "tipo_vehiculo_id": v.tipo_vehiculo_id,
        "tipo_vehiculo": {
            "id": v.tipo_vehiculo.id,
            "codigo": v.tipo_vehiculo.codigo,
            "nombre": v.tipo_vehiculo.nombre,
        } if v.tipo_vehiculo else None,
        "label": _label(v),
    }


def _label(v: Vehiculo) -> str:
    """Etiqueta para mostrar en selectores."""
    parts = [v.patente]
    if v.marca:
        parts.append(v.marca)
    if v.modelo:
        parts.append(v.modelo)
    if v.tipo_vehiculo:
        parts.append(f"({v.tipo_vehiculo.nombre})")
    return " — ".join(parts)


# ──────────────────────────────────────────
# Tipos de Vehículo (solo lectura, viene de tipos_vehiculo existente)
# ──────────────────────────────────────────

@router.get("/tipos")
def listar_tipos_vehiculo(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista los tipos de vehículo disponibles."""
    tipos = db.query(TipoVehiculo).filter(TipoVehiculo.activo == True).all()
    return [{"id": t.id, "codigo": t.codigo, "nombre": t.nombre} for t in tipos]


# ──────────────────────────────────────────
# Vehículos CRUD
# ──────────────────────────────────────────

@router.get("/")
def listar_vehiculos(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista vehículos del tenant."""
    q = db.query(Vehiculo).filter(Vehiculo.tenant_id == current_user.tenant_id)
    if solo_activos:
        q = q.filter(Vehiculo.activo == True)
    vehiculos = q.options(joinedload(Vehiculo.tipo_vehiculo)).order_by(Vehiculo.patente).all()
    return [_vehiculo_out(v) for v in vehiculos]


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_vehiculo(
    data: VehiculoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Crea un nuevo vehículo."""
    # Validar patente única por tenant
    existe = db.query(Vehiculo).filter(
        Vehiculo.tenant_id == current_user.tenant_id,
        Vehiculo.patente == data.patente.upper(),
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail=f"Ya existe un vehículo con patente {data.patente}")

    # Validar tipo si se envió
    if data.tipo_vehiculo_id:
        tipo = db.query(TipoVehiculo).filter(TipoVehiculo.id == data.tipo_vehiculo_id).first()
        if not tipo:
            raise HTTPException(status_code=404, detail="Tipo de vehículo no encontrado")

    v = Vehiculo(
        tenant_id=current_user.tenant_id,
        patente=data.patente.upper(),
        marca=data.marca,
        modelo=data.modelo,
        anio=data.anio,
        capacidad_kg=data.capacidad_kg,
        tipo_vehiculo_id=data.tipo_vehiculo_id,
        activo=True,
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    v = db.query(Vehiculo).filter(Vehiculo.id == v.id).options(joinedload(Vehiculo.tipo_vehiculo)).first()
    return _vehiculo_out(v)


@router.get("/choferes")
def listar_choferes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lista usuarios activos del tenant con rol DESPACHADOR."""
    users = (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .filter(
            User.tenant_id == current_user.tenant_id,
            User.is_active == True,
            Role.nombre.ilike('despachador'),
        )
        .order_by(User.nombre_completo)
        .all()
    )
    return [{"id": u.id, "nombre_completo": u.nombre_completo, "email": u.email, "is_active": u.is_active} for u in users]


@router.get("/{vehiculo_id}")
def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    v = db.query(Vehiculo).filter(
        Vehiculo.id == vehiculo_id,
        Vehiculo.tenant_id == current_user.tenant_id,
    ).options(joinedload(Vehiculo.tipo_vehiculo)).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return _vehiculo_out(v)


@router.put("/{vehiculo_id}")
def actualizar_vehiculo(
    vehiculo_id: int,
    data: VehiculoUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    v = db.query(Vehiculo).filter(
        Vehiculo.id == vehiculo_id,
        Vehiculo.tenant_id == current_user.tenant_id,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")

    if data.patente is not None:
        nueva = data.patente.upper()
        if nueva != v.patente:
            existe = db.query(Vehiculo).filter(
                Vehiculo.tenant_id == current_user.tenant_id,
                Vehiculo.patente == nueva,
                Vehiculo.id != vehiculo_id,
            ).first()
            if existe:
                raise HTTPException(status_code=400, detail=f"Ya existe un vehículo con patente {nueva}")
        v.patente = nueva

    if data.marca is not None:
        v.marca = data.marca
    if data.modelo is not None:
        v.modelo = data.modelo
    if data.anio is not None:
        v.anio = data.anio
    if data.capacidad_kg is not None:
        v.capacidad_kg = data.capacidad_kg
    if data.tipo_vehiculo_id is not None:
        v.tipo_vehiculo_id = data.tipo_vehiculo_id
    if data.activo is not None:
        v.activo = data.activo

    db.commit()
    v = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).options(joinedload(Vehiculo.tipo_vehiculo)).first()
    return _vehiculo_out(v)


@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Desactiva un vehículo (no se elimina físicamente)."""
    v = db.query(Vehiculo).filter(
        Vehiculo.id == vehiculo_id,
        Vehiculo.tenant_id == current_user.tenant_id,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    v.activo = False
    db.commit()
