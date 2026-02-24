from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import PaletaColores
from schemas.paleta_colores import PaletaColoresCreate, PaletaColoresUpdate, PaletaColoresResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[PaletaColoresResponse])
def listar_paletas_colores(db: Session = Depends(get_db)):
    return db.query(PaletaColores).all()

@router.get("/{paleta_id}", response_model=PaletaColoresResponse)
def obtener_paleta_colores(paleta_id: int, db: Session = Depends(get_db)):
    paleta = db.query(PaletaColores).get(paleta_id)
    if not paleta:
        raise HTTPException(status_code=404, detail="Paleta no encontrada")
    return paleta

@router.post("/", response_model=PaletaColoresResponse)
def crear_paleta_colores(data: PaletaColoresCreate, db: Session = Depends(get_db)):
    paleta = PaletaColores(**data.dict())
    db.add(paleta)
    db.commit()
    db.refresh(paleta)
    return paleta

@router.put("/{paleta_id}", response_model=PaletaColoresResponse)
def actualizar_paleta_colores(paleta_id: int, data: PaletaColoresUpdate, db: Session = Depends(get_db)):
    paleta = db.query(PaletaColores).get(paleta_id)
    if not paleta:
        raise HTTPException(status_code=404, detail="Paleta no encontrada")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(paleta, key, value)
    db.commit()
    db.refresh(paleta)
    return paleta

@router.delete("/{paleta_id}", response_model=dict)
def eliminar_paleta_colores(paleta_id: int, db: Session = Depends(get_db)):
    paleta = db.query(PaletaColores).get(paleta_id)
    if not paleta:
        raise HTTPException(status_code=404, detail="Paleta no encontrada")
    db.delete(paleta)
    db.commit()
    return {"ok": True}
