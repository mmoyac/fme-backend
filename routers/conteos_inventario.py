"""
Router de Conteo de Inventario (change OpenSpec: add-conteo-inventario).

IMPORTANTE: endpoints `def` síncronos (BD síncrona). Ver incidente 2026-11-11.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from database.database import get_db
from routers.auth import get_current_active_user
from schemas.conteo_inventario import (
    ConteoAgregarItems, ConteoCreate, ConteoDetalle, ConteoItemResponse, ConteoItemUpdate, ConteoResumen,
)
from services import conteo_inventario_service as svc

router = APIRouter()


@router.post("/", response_model=ConteoDetalle, status_code=status.HTTP_201_CREATED)
def iniciar_conteo(data: ConteoCreate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    """Inicia un conteo COMPLETO (precarga productos del local) o PARCIAL (vacío)."""
    conteo = svc.iniciar_conteo(db, current_user, data.local_id, data.tipo, data.observacion)
    return svc.obtener_detalle(db, current_user, conteo.id)


@router.get("/", response_model=List[ConteoResumen])
def listar_conteos(
    local_id: Optional[int] = None,
    estado: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    usuario_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return svc.listar_conteos(db, current_user, local_id, estado, desde, hasta, usuario_id, limit, offset)


@router.get("/{conteo_id}", response_model=ConteoDetalle)
def obtener_conteo(conteo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    return svc.obtener_detalle(db, current_user, conteo_id)


@router.post("/{conteo_id}/items", response_model=ConteoDetalle)
def agregar_items(
    conteo_id: int, data: ConteoAgregarItems,
    db: Session = Depends(get_db), current_user=Depends(get_current_active_user),
):
    svc.agregar_items(db, current_user, conteo_id, data.producto_ids, data.categoria_id)
    return svc.obtener_detalle(db, current_user, conteo_id)


@router.delete("/{conteo_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_item(conteo_id: int, item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    svc.quitar_item(db, current_user, conteo_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{conteo_id}/items/{item_id}", response_model=ConteoItemResponse)
def registrar_cantidad(
    conteo_id: int, item_id: int, data: ConteoItemUpdate,
    db: Session = Depends(get_db), current_user=Depends(get_current_active_user),
):
    item = svc.registrar_cantidad(db, current_user, conteo_id, item_id, data.cantidad_contada)
    return svc.serializar_item(item)


@router.post("/{conteo_id}/finalizar", response_model=ConteoDetalle)
def finalizar_conteo(conteo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    """Ajusta el stock por diferencia (movimientos AJUSTE_CONTEO) y cierra el conteo."""
    svc.finalizar_conteo(db, current_user, conteo_id)
    return svc.obtener_detalle(db, current_user, conteo_id)


@router.post("/{conteo_id}/cancelar", response_model=ConteoDetalle)
def cancelar_conteo(conteo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    svc.cancelar_conteo(db, current_user, conteo_id)
    return svc.obtener_detalle(db, current_user, conteo_id)


@router.get("/{conteo_id}/excel")
def exportar_excel(conteo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contenido, nombre = svc.exportar_excel(db, current_user, conteo_id)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
