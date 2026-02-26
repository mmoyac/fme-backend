"""
Router para gestión de tablas maestras (Categorías, Tipos, Unidades de Medida).
"""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from database.models import CategoriaProducto as CategoriaProductoModel
from database.models import TipoProducto as TipoProductoModel
from database.models import TipoDocumento as TipoDocumentoModel
from database.models import UnidadMedida as UnidadMedidaModel
from database.models import MedioPago as MedioPagoModel
from database.models import EstadoCheque as EstadoChequeModel
from database.models import Banco as BancoModel
from database.models import TipoVehiculo as TipoVehiculoModel
from database.models import EstadoEnrolamiento as EstadoEnrolamientoModel
from database.models import Ubicacion as UbicacionModel
from database.models import TipoVenta as TipoVentaModel
from database.models import TipoProveedor as TipoProveedorModel
from database.models import User
from schemas.maestras import (
    CategoriaProducto, CategoriaProductoCreate, CategoriaProductoUpdate,
    TipoProducto, TipoProductoCreate, TipoProductoUpdate,
    TipoDocumento, TipoDocumentoCreate, TipoDocumentoUpdate,
    UnidadMedida, UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaConBase,
    MedioPago, MedioPagoCreate, MedioPagoUpdate,
    EstadoCheque, EstadoChequeCreate, EstadoChequeUpdate,
    Banco, BancoCreate, BancoUpdate,
    TipoVenta, TipoVentaCreate, TipoVentaUpdate,
    TipoProveedor, TipoProveedorCreate, TipoProveedorUpdate,
    TipoVehiculo, TipoVehiculoCreate, TipoVehiculoUpdate,
    EstadoEnrolamiento, EstadoEnrolamientoCreate, EstadoEnrolamientoUpdate,
    Ubicacion, UbicacionCreate, UbicacionUpdate
)
from routers.auth import get_current_active_user

router = APIRouter()


# Dependencia para verificar que el usuario es admin
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role.nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user


# ============================================
# CATEGORÍAS DE PRODUCTO
# ============================================

@router.get("/categorias", response_model=List[CategoriaProducto])
def listar_categorias(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar categorías de productos (tabla maestra global)."""
    query = db.query(CategoriaProductoModel).options(joinedload(CategoriaProductoModel.tipo_venta))
    
    if activo is not None:
        query = query.filter(CategoriaProductoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/categorias/{categoria_id}", response_model=CategoriaProducto)
def obtener_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener una categoría por ID (tabla maestra global)."""
    categoria = db.query(CategoriaProductoModel).options(joinedload(CategoriaProductoModel.tipo_venta)).filter(
        CategoriaProductoModel.id == categoria_id
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@router.post("/categorias", response_model=CategoriaProducto, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria: CategoriaProductoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear una nueva categoría de producto (tabla maestra global)."""
    # Verificar código único
    existing = db.query(CategoriaProductoModel).filter(
        CategoriaProductoModel.codigo == categoria.codigo
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{categoria.codigo}' ya existe")
    
    db_categoria = CategoriaProductoModel(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.put("/categorias/{categoria_id}", response_model=CategoriaProducto)
def actualizar_categoria(
    categoria_id: int,
    categoria: CategoriaProductoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar una categoría existente (tabla maestra global)."""
    db_categoria = db.query(CategoriaProductoModel).filter(
        CategoriaProductoModel.id == categoria_id
    ).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar código único si se está actualizando
    if categoria.codigo and categoria.codigo != db_categoria.codigo:
        existing = db.query(CategoriaProductoModel).filter(
            CategoriaProductoModel.codigo == categoria.codigo
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{categoria.codigo}' ya existe")
    
    update_data = categoria.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_categoria, field, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar una categoría (solo si no tiene productos asociados) - tabla maestra global."""
    db_categoria = db.query(CategoriaProductoModel).filter(
        CategoriaProductoModel.id == categoria_id
    ).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si tiene productos asociados
    if db_categoria.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría porque tiene {len(db_categoria.productos)} productos asociados"
        )
    
    db.delete(db_categoria)
    db.commit()
    return None


# ============================================
# TIPOS DE PRODUCTO
# ============================================

@router.get("/tipos", response_model=List[TipoProducto])
def listar_tipos(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de productos (tabla maestra global)."""
    query = db.query(TipoProductoModel)
    
    if activo is not None:
        query = query.filter(TipoProductoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/tipos/{tipo_id}", response_model=TipoProducto)
def obtener_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un tipo de producto por ID (tabla maestra global)."""
    tipo = db.query(TipoProductoModel).filter(
        TipoProductoModel.id == tipo_id
    ).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    return tipo


@router.post("/tipos", response_model=TipoProducto, status_code=status.HTTP_201_CREATED)
def crear_tipo(
    tipo: TipoProductoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de producto (tabla maestra global)."""
    # Verificar código único
    existing = db.query(TipoProductoModel).filter(
        TipoProductoModel.codigo == tipo.codigo
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    db_tipo = TipoProductoModel(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.put("/tipos/{tipo_id}", response_model=TipoProducto)
def actualizar_tipo(
    tipo_id: int,
    tipo: TipoProductoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de producto existente (tabla maestra global)."""
    db_tipo = db.query(TipoProductoModel).filter(
        TipoProductoModel.id == tipo_id
    ).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    
    # Verificar código único si se está actualizando
    if tipo.codigo and tipo.codigo != db_tipo.codigo:
        existing = db.query(TipoProductoModel).filter(
            TipoProductoModel.codigo == tipo.codigo
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    update_data = tipo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo, field, value)
    
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.delete("/tipos/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de producto (solo si no tiene productos asociados) - tabla maestra global."""
    db_tipo = db.query(TipoProductoModel).filter(
        TipoProductoModel.id == tipo_id
    ).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    
    # Verificar si tiene productos asociados
    if db_tipo.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo porque tiene {len(db_tipo.productos)} productos asociados"
        )
    
    db.delete(db_tipo)
    db.commit()
    return None

# ============================================
# TIPOS DE DOCUMENTO
# ============================================

@router.get("/tipos-documento", response_model=List[TipoDocumento])
def listar_tipos_documento(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de documento tributario."""
    query = db.query(TipoDocumentoModel)
    
    if activo is not None:
        query = query.filter(TipoDocumentoModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/tipos-documento/{tipo_id}", response_model=TipoDocumento)
def obtener_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un tipo de documento por ID."""
    tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    return tipo


@router.post("/tipos-documento", response_model=TipoDocumento, status_code=status.HTTP_201_CREATED)
def crear_tipo_documento(
    tipo: TipoDocumentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de documento."""
    # Verificar código único
    existing = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.codigo == tipo.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    db_tipo = TipoDocumentoModel(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.put("/tipos-documento/{tipo_id}", response_model=TipoDocumento)
def actualizar_tipo_documento(
    tipo_id: int,
    tipo: TipoDocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de documento existente."""
    db_tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    
    # Verificar código único si se está actualizando
    if tipo.codigo and tipo.codigo != db_tipo.codigo:
        existing = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.codigo == tipo.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{tipo.codigo}' ya existe")
    
    update_data = tipo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo, field, value)
    
    db.commit()
    db.refresh(db_tipo)
    return db_tipo


@router.delete("/tipos-documento/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de documento (solo si no tiene compras asociadas)."""
    db_tipo = db.query(TipoDocumentoModel).filter(TipoDocumentoModel.id == tipo_id).first()
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    
    # Verificar si tiene compras asociadas
    if db_tipo.compras:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo porque tiene {len(db_tipo.compras)} compras asociadas"
        )
    
    db.delete(db_tipo)
    db.commit()
    return None


# ============================================
# UNIDADES DE MEDIDA
# ============================================

@router.get("/unidades", response_model=List[UnidadMedidaConBase])
def listar_unidades(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar unidades de medida."""
    query = db.query(UnidadMedidaModel)
    
    if activo is not None:
        query = query.filter(UnidadMedidaModel.activo == activo)
    
    if tipo:
        query = query.filter(UnidadMedidaModel.tipo == tipo)
    
    return query.offset(skip).limit(limit).all()


@router.get("/unidades/{unidad_id}", response_model=UnidadMedidaConBase)
def obtener_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener una unidad de medida por ID."""
    unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    return unidad


@router.post("/unidades", response_model=UnidadMedida, status_code=status.HTTP_201_CREATED)
def crear_unidad(
    unidad: UnidadMedidaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear una nueva unidad de medida."""
    # Verificar código único
    existing = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.codigo == unidad.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código '{unidad.codigo}' ya existe")
    
    # Verificar que la unidad base existe si se especifica
    if unidad.unidad_base_id:
        unidad_base = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad.unidad_base_id).first()
        if not unidad_base:
            raise HTTPException(status_code=400, detail="La unidad base especificada no existe")
    
    db_unidad = UnidadMedidaModel(**unidad.model_dump())
    db.add(db_unidad)
    db.commit()
    db.refresh(db_unidad)
    return db_unidad


@router.put("/unidades/{unidad_id}", response_model=UnidadMedida)
def actualizar_unidad(
    unidad_id: int,
    unidad: UnidadMedidaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar una unidad de medida existente."""
    db_unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    
    # Verificar código único si se está actualizando
    if unidad.codigo and unidad.codigo != db_unidad.codigo:
        existing = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.codigo == unidad.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El código '{unidad.codigo}' ya existe")
    
    # Verificar que la unidad base existe si se especifica
    if unidad.unidad_base_id:
        unidad_base = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad.unidad_base_id).first()
        if not unidad_base:
            raise HTTPException(status_code=400, detail="La unidad base especificada no existe")
    
    update_data = unidad.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_unidad, field, value)
    
    db.commit()
    db.refresh(db_unidad)
    return db_unidad


@router.delete("/unidades/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar una unidad de medida (solo si no tiene productos asociados)."""
    db_unidad = db.query(UnidadMedidaModel).filter(UnidadMedidaModel.id == unidad_id).first()
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    
    # Verificar si tiene productos asociados
    if db_unidad.productos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la unidad porque tiene {len(db_unidad.productos)} productos asociados"
        )
    
    db.delete(db_unidad)
    db.commit()
    return None


# ============================================
# MEDIOS DE PAGO
# ============================================

@router.get("/medios-pago", response_model=List[MedioPago])
def listar_medios_pago(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar medios de pago."""
    query = db.query(MedioPagoModel)
    
    if activo is not None:
        query = query.filter(MedioPagoModel.activo == activo)
    
    medios_pago = query.offset(skip).limit(limit).all()
    return medios_pago


@router.post("/medios-pago", response_model=MedioPago)
def crear_medio_pago(
    medio_pago: MedioPagoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo medio de pago."""
    # Verificar que el código no exista
    existing = db.query(MedioPagoModel).filter(MedioPagoModel.codigo == medio_pago.codigo).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un medio de pago con el código {medio_pago.codigo}"
        )
    
    db_medio_pago = MedioPagoModel(**medio_pago.model_dump())
    db.add(db_medio_pago)
    db.commit()
    db.refresh(db_medio_pago)
    return db_medio_pago


@router.get("/medios-pago/{medio_pago_id}", response_model=MedioPago)
def obtener_medio_pago(
    medio_pago_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un medio de pago por ID."""
    db_medio_pago = db.query(MedioPagoModel).filter(MedioPagoModel.id == medio_pago_id).first()
    if not db_medio_pago:
        raise HTTPException(status_code=404, detail="Medio de pago no encontrado")
    return db_medio_pago


@router.put("/medios-pago/{medio_pago_id}", response_model=MedioPago)
def actualizar_medio_pago(
    medio_pago_id: int,
    medio_pago_update: MedioPagoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un medio de pago."""
    db_medio_pago = db.query(MedioPagoModel).filter(MedioPagoModel.id == medio_pago_id).first()
    if not db_medio_pago:
        raise HTTPException(status_code=404, detail="Medio de pago no encontrado")
    
    # Verificar que el código no exista en otro registro
    if medio_pago_update.codigo:
        existing = db.query(MedioPagoModel).filter(
            MedioPagoModel.codigo == medio_pago_update.codigo,
            MedioPagoModel.id != medio_pago_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro medio de pago con el código {medio_pago_update.codigo}"
            )
    
    # Actualizar solo los campos que no son None
    update_data = medio_pago_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_medio_pago, field, value)
    
    db.commit()
    db.refresh(db_medio_pago)
    return db_medio_pago


@router.delete("/medios-pago/{medio_pago_id}")
def eliminar_medio_pago(
    medio_pago_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un medio de pago."""
    db_medio_pago = db.query(MedioPagoModel).filter(MedioPagoModel.id == medio_pago_id).first()
    if not db_medio_pago:
        raise HTTPException(status_code=404, detail="Medio de pago no encontrado")
    
    # Verificar si tiene referencias (cuando se implemente)
    # if db_medio_pago.compras or db_medio_pago.pedidos:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="No se puede eliminar el medio de pago porque tiene transacciones asociadas"
    #     )
    
    db.delete(db_medio_pago)
    db.commit()
    return None


# ============================================
# ESTADOS DE CHEQUE
# ============================================

@router.get("/estados-cheque", response_model=List[EstadoCheque])
def listar_estados_cheque(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar estados de cheque."""
    query = db.query(EstadoChequeModel)
    
    if activo is not None:
        query = query.filter(EstadoChequeModel.activo == activo)
    
    estados = query.offset(skip).limit(limit).all()
    return estados


@router.post("/estados-cheque", response_model=EstadoCheque)
def crear_estado_cheque(
    estado: EstadoChequeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo estado de cheque."""
    # Verificar que el código no exista
    existing = db.query(EstadoChequeModel).filter(EstadoChequeModel.codigo == estado.codigo).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un estado de cheque con el código {estado.codigo}"
        )
    
    db_estado = EstadoChequeModel(**estado.model_dump())
    db.add(db_estado)
    db.commit()
    db.refresh(db_estado)
    return db_estado


@router.get("/estados-cheque/{estado_id}", response_model=EstadoCheque)
def obtener_estado_cheque(
    estado_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un estado de cheque por ID."""
    db_estado = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == estado_id).first()
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado de cheque no encontrado")
    return db_estado


@router.put("/estados-cheque/{estado_id}", response_model=EstadoCheque)
def actualizar_estado_cheque(
    estado_id: int,
    estado_update: EstadoChequeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un estado de cheque."""
    db_estado = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == estado_id).first()
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado de cheque no encontrado")
    
    # Verificar que el código no exista en otro registro
    if estado_update.codigo:
        existing = db.query(EstadoChequeModel).filter(
            EstadoChequeModel.codigo == estado_update.codigo,
            EstadoChequeModel.id != estado_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro estado de cheque con el código {estado_update.codigo}"
            )
    
    # Actualizar solo los campos que no son None
    update_data = estado_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_estado, field, value)
    
    db.commit()
    db.refresh(db_estado)
    return db_estado


@router.delete("/estados-cheque/{estado_id}")
def eliminar_estado_cheque(
    estado_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un estado de cheque."""
    db_estado = db.query(EstadoChequeModel).filter(EstadoChequeModel.id == estado_id).first()
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado de cheque no encontrado")
    
    # Verificar si tiene referencias (cuando se implemente)
    # if db_estado.cheques:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="No se puede eliminar el estado porque tiene cheques asociados"
    #     )
    
    db.delete(db_estado)
    db.commit()
    return None


# ============================================
# BANCOS
# ============================================

@router.get("/bancos", response_model=List[Banco])
def listar_bancos(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar bancos."""
    query = db.query(BancoModel)
    
    if activo is not None:
        query = query.filter(BancoModel.activo == activo)
    
    bancos = query.offset(skip).limit(limit).all()
    return bancos


@router.post("/bancos", response_model=Banco)
def crear_banco(
    banco: BancoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo banco."""
    # Verificar que el código no exista
    existing = db.query(BancoModel).filter(BancoModel.codigo == banco.codigo).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un banco con el código {banco.codigo}"
        )
    
    db_banco = BancoModel(**banco.model_dump())
    db.add(db_banco)
    db.commit()
    db.refresh(db_banco)
    return db_banco


@router.get("/bancos/{banco_id}", response_model=Banco)
def obtener_banco(
    banco_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un banco por ID."""
    db_banco = db.query(BancoModel).filter(BancoModel.id == banco_id).first()
    if not db_banco:
        raise HTTPException(status_code=404, detail="Banco no encontrado")
    return db_banco


@router.put("/bancos/{banco_id}", response_model=Banco)
def actualizar_banco(
    banco_id: int,
    banco_update: BancoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un banco."""
    db_banco = db.query(BancoModel).filter(BancoModel.id == banco_id).first()
    if not db_banco:
        raise HTTPException(status_code=404, detail="Banco no encontrado")
    
    # Verificar que el código no exista en otro registro
    if banco_update.codigo:
        existing = db.query(BancoModel).filter(
            BancoModel.codigo == banco_update.codigo,
            BancoModel.id != banco_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro banco con el código {banco_update.codigo}"
            )
    
    # Actualizar solo los campos que no son None
    update_data = banco_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_banco, field, value)
    
    db.commit()
    db.refresh(db_banco)
    return db_banco


@router.delete("/bancos/{banco_id}")
def eliminar_banco(
    banco_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un banco."""
    db_banco = db.query(BancoModel).filter(BancoModel.id == banco_id).first()
    if not db_banco:
        raise HTTPException(status_code=404, detail="Banco no encontrado")
    
    # Verificar si tiene cheques asociados
    if db_banco.cheques:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el banco porque tiene {len(db_banco.cheques)} cheques asociados"
        )
    
    db.delete(db_banco)
    db.commit()
    return None


# ============================================
# TIPOS DE VENTA
# ============================================

@router.get("/tipos-venta", response_model=List[TipoVenta])
def listar_tipos_venta(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de venta."""
    query = db.query(TipoVentaModel)
    
    if activo is not None:
        query = query.filter(TipoVentaModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.post("/tipos-venta", response_model=TipoVenta, status_code=status.HTTP_201_CREATED)
def crear_tipo_venta(
    tipo_venta: TipoVentaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de venta."""
    # Verificar que el código no exista
    existing = db.query(TipoVentaModel).filter(TipoVentaModel.codigo == tipo_venta.codigo).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un tipo de venta con el código {tipo_venta.codigo}"
        )
    
    db_tipo_venta = TipoVentaModel(**tipo_venta.model_dump())
    db.add(db_tipo_venta)
    db.commit()
    db.refresh(db_tipo_venta)
    return db_tipo_venta


@router.put("/tipos-venta/{tipo_venta_id}", response_model=TipoVenta)
def actualizar_tipo_venta(
    tipo_venta_id: int,
    tipo_venta_update: TipoVentaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de venta."""
    db_tipo_venta = db.query(TipoVentaModel).filter(TipoVentaModel.id == tipo_venta_id).first()
    if not db_tipo_venta:
        raise HTTPException(status_code=404, detail="Tipo de venta no encontrado")
    
    # Verificar que el código no exista en otro registro
    if tipo_venta_update.codigo:
        existing = db.query(TipoVentaModel).filter(
            TipoVentaModel.codigo == tipo_venta_update.codigo,
            TipoVentaModel.id != tipo_venta_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro tipo de venta con el código {tipo_venta_update.codigo}"
            )
    
    # Actualizar solo los campos que no son None
    update_data = tipo_venta_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo_venta, field, value)
    
    db.commit()
    db.refresh(db_tipo_venta)
    return db_tipo_venta


@router.delete("/tipos-venta/{tipo_venta_id}")
def eliminar_tipo_venta(
    tipo_venta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de venta."""
    db_tipo_venta = db.query(TipoVentaModel).filter(TipoVentaModel.id == tipo_venta_id).first()
    if not db_tipo_venta:
        raise HTTPException(status_code=404, detail="Tipo de venta no encontrado")
    
    # Verificar si tiene categorías asociadas
    if db_tipo_venta.categorias:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo de venta porque tiene {len(db_tipo_venta.categorias)} categorías asociadas"
        )
    
    db.delete(db_tipo_venta)
    db.commit()
    return None


# ============================================
# TIPOS DE PROVEEDOR
# ============================================

@router.get("/tipos-proveedor", response_model=List[TipoProveedor])
def listar_tipos_proveedor(
    skip: int = 0,
    limit: int = 100,
    activo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar tipos de proveedor."""
    query = db.query(TipoProveedorModel)
    
    if activo is not None:
        query = query.filter(TipoProveedorModel.activo == activo)
    
    return query.offset(skip).limit(limit).all()


@router.post("/tipos-proveedor", response_model=TipoProveedor, status_code=status.HTTP_201_CREATED)
def crear_tipo_proveedor(
    tipo_proveedor: TipoProveedorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de proveedor."""
    # Verificar que el código no exista
    existing = db.query(TipoProveedorModel).filter(TipoProveedorModel.codigo == tipo_proveedor.codigo).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un tipo de proveedor con el código {tipo_proveedor.codigo}"
        )
    
    db_tipo_proveedor = TipoProveedorModel(**tipo_proveedor.model_dump())
    db.add(db_tipo_proveedor)
    db.commit()
    db.refresh(db_tipo_proveedor)
    return db_tipo_proveedor


@router.put("/tipos-proveedor/{tipo_proveedor_id}", response_model=TipoProveedor)
def actualizar_tipo_proveedor(
    tipo_proveedor_id: int,
    tipo_proveedor_update: TipoProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de proveedor."""
    db_tipo_proveedor = db.query(TipoProveedorModel).filter(TipoProveedorModel.id == tipo_proveedor_id).first()
    if not db_tipo_proveedor:
        raise HTTPException(status_code=404, detail="Tipo de proveedor no encontrado")
    
    # Verificar que el código no exista en otro registro
    if tipo_proveedor_update.codigo:
        existing = db.query(TipoProveedorModel).filter(
            TipoProveedorModel.codigo == tipo_proveedor_update.codigo,
            TipoProveedorModel.id != tipo_proveedor_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro tipo de proveedor con el código {tipo_proveedor_update.codigo}"
            )
    
    # Actualizar solo los campos que no son None
    update_data = tipo_proveedor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo_proveedor, field, value)
    
    db.commit()
    db.refresh(db_tipo_proveedor)
    return db_tipo_proveedor


@router.delete("/tipos-proveedor/{tipo_proveedor_id}")
def eliminar_tipo_proveedor(
    tipo_proveedor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de proveedor."""
    db_tipo_proveedor = db.query(TipoProveedorModel).filter(TipoProveedorModel.id == tipo_proveedor_id).first()
    if not db_tipo_proveedor:
        raise HTTPException(status_code=404, detail="Tipo de proveedor no encontrado")
    
    # Verificar si tiene proveedores asociados
    if db_tipo_proveedor.proveedores:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo de proveedor porque tiene {len(db_tipo_proveedor.proveedores)} proveedores asociados"
        )
    
    db.delete(db_tipo_proveedor)
    db.commit()
    return None


# ============================================
# TIPOS DE VEHÍCULO
# ============================================

@router.get("/tipos-vehiculo", response_model=List[TipoVehiculo])
def listar_tipos_vehiculo(db: Session = Depends(get_db)):
    """Listar todos los tipos de vehículo."""
    return db.query(TipoVehiculoModel).filter(TipoVehiculoModel.activo == True).all()


@router.post("/tipos-vehiculo", response_model=TipoVehiculo, status_code=status.HTTP_201_CREATED)
def crear_tipo_vehiculo(
    tipo_vehiculo: TipoVehiculoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo tipo de vehículo."""
    # Verificar código único
    db_tipo_vehiculo = db.query(TipoVehiculoModel).filter(TipoVehiculoModel.codigo == tipo_vehiculo.codigo).first()
    if db_tipo_vehiculo:
        raise HTTPException(status_code=400, detail="Ya existe un tipo de vehículo con este código")
    
    db_tipo_vehiculo = TipoVehiculoModel(**tipo_vehiculo.model_dump())
    db.add(db_tipo_vehiculo)
    db.commit()
    db.refresh(db_tipo_vehiculo)
    return db_tipo_vehiculo


@router.put("/tipos-vehiculo/{tipo_vehiculo_id}", response_model=TipoVehiculo)
def actualizar_tipo_vehiculo(
    tipo_vehiculo_id: int,
    tipo_vehiculo: TipoVehiculoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un tipo de vehículo."""
    db_tipo_vehiculo = db.query(TipoVehiculoModel).filter(TipoVehiculoModel.id == tipo_vehiculo_id).first()
    if not db_tipo_vehiculo:
        raise HTTPException(status_code=404, detail="Tipo de vehículo no encontrado")
    
    # Verificar código único si se está cambiando
    if tipo_vehiculo.codigo and tipo_vehiculo.codigo != db_tipo_vehiculo.codigo:
        existing = db.query(TipoVehiculoModel).filter(TipoVehiculoModel.codigo == tipo_vehiculo.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un tipo de vehículo con este código")
    
    # Actualizar solo los campos proporcionados
    update_data = tipo_vehiculo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipo_vehiculo, field, value)
    
    db.commit()
    db.refresh(db_tipo_vehiculo)
    return db_tipo_vehiculo


@router.delete("/tipos-vehiculo/{tipo_vehiculo_id}")
def eliminar_tipo_vehiculo(
    tipo_vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un tipo de vehículo."""
    db_tipo_vehiculo = db.query(TipoVehiculoModel).filter(TipoVehiculoModel.id == tipo_vehiculo_id).first()
    if not db_tipo_vehiculo:
        raise HTTPException(status_code=404, detail="Tipo de vehículo no encontrado")
    
    # Verificar si tiene enrolamientos asociados
    if db_tipo_vehiculo.enrolamientos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el tipo de vehículo porque tiene {len(db_tipo_vehiculo.enrolamientos)} enrolamientos asociados"
        )
    
    db.delete(db_tipo_vehiculo)
    db.commit()
    return None


# ============================================
# ESTADOS DE ENROLAMIENTO
# ============================================

@router.get("/estados-enrolamiento", response_model=List[EstadoEnrolamiento])
def listar_estados_enrolamiento(db: Session = Depends(get_db)):
    """Listar todos los estados de enrolamiento."""
    return db.query(EstadoEnrolamientoModel).all()


@router.post("/estados-enrolamiento", response_model=EstadoEnrolamiento, status_code=status.HTTP_201_CREATED)
def crear_estado_enrolamiento(
    estado: EstadoEnrolamientoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear un nuevo estado de enrolamiento."""
    # Verificar código único
    db_estado = db.query(EstadoEnrolamientoModel).filter(EstadoEnrolamientoModel.codigo == estado.codigo).first()
    if db_estado:
        raise HTTPException(status_code=400, detail="Ya existe un estado de enrolamiento con este código")
    
    db_estado = EstadoEnrolamientoModel(**estado.model_dump())
    db.add(db_estado)
    db.commit()
    db.refresh(db_estado)
    return db_estado


@router.put("/estados-enrolamiento/{estado_id}", response_model=EstadoEnrolamiento)
def actualizar_estado_enrolamiento(
    estado_id: int,
    estado: EstadoEnrolamientoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar un estado de enrolamiento."""
    db_estado = db.query(EstadoEnrolamientoModel).filter(EstadoEnrolamientoModel.id == estado_id).first()
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado de enrolamiento no encontrado")
    
    # Verificar código único si se está cambiando
    if estado.codigo and estado.codigo != db_estado.codigo:
        existing = db.query(EstadoEnrolamientoModel).filter(EstadoEnrolamientoModel.codigo == estado.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un estado de enrolamiento con este código")
    
    # Actualizar solo los campos proporcionados
    update_data = estado.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_estado, field, value)
    
    db.commit()
    db.refresh(db_estado)
    return db_estado


@router.delete("/estados-enrolamiento/{estado_id}")
def eliminar_estado_enrolamiento(
    estado_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar un estado de enrolamiento."""
    db_estado = db.query(EstadoEnrolamientoModel).filter(EstadoEnrolamientoModel.id == estado_id).first()
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado de enrolamiento no encontrado")
    
    # Verificar si tiene enrolamientos asociados
    if db_estado.enrolamientos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el estado porque tiene {len(db_estado.enrolamientos)} enrolamientos asociados"
        )
    
    db.delete(db_estado)
    db.commit()
    return None


# ============================================
# UBICACIONES
# ============================================

@router.get("/ubicaciones", response_model=List[Ubicacion])
def listar_ubicaciones(db: Session = Depends(get_db)):
    """Listar todas las ubicaciones activas."""
    return db.query(UbicacionModel).all()


@router.post("/ubicaciones", response_model=Ubicacion, status_code=status.HTTP_201_CREATED)
def crear_ubicacion(
    ubicacion: UbicacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Crear una nueva ubicación."""
    # Verificar código único
    db_ubicacion = db.query(UbicacionModel).filter(UbicacionModel.codigo == ubicacion.codigo).first()
    if db_ubicacion:
        raise HTTPException(status_code=400, detail="Ya existe una ubicación con este código")
    
    db_ubicacion = UbicacionModel(**ubicacion.model_dump())
    db.add(db_ubicacion)
    db.commit()
    db.refresh(db_ubicacion)
    return db_ubicacion


@router.put("/ubicaciones/{ubicacion_id}", response_model=Ubicacion)
def actualizar_ubicacion(
    ubicacion_id: int,
    ubicacion: UbicacionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Actualizar una ubicación."""
    db_ubicacion = db.query(UbicacionModel).filter(UbicacionModel.id == ubicacion_id).first()
    if not db_ubicacion:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Verificar código único si se está cambiando
    if ubicacion.codigo and ubicacion.codigo != db_ubicacion.codigo:
        existing = db.query(UbicacionModel).filter(UbicacionModel.codigo == ubicacion.codigo).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe una ubicación con este código")
    
    # Actualizar solo los campos proporcionados
    update_data = ubicacion.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ubicacion, field, value)
    
    db.commit()
    db.refresh(db_ubicacion)
    return db_ubicacion


@router.delete("/ubicaciones/{ubicacion_id}")
def eliminar_ubicacion(
    ubicacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Eliminar una ubicación."""
    db_ubicacion = db.query(UbicacionModel).filter(UbicacionModel.id == ubicacion_id).first()
    if not db_ubicacion:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Verificar si tiene lotes asociados
    if db_ubicacion.lotes:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la ubicación porque tiene {len(db_ubicacion.lotes)} lotes asociados"
        )
    
    db.delete(db_ubicacion)
    db.commit()
    return None


# ============================================
# TIPOS DE DOCUMENTO TRIBUTARIO
# ============================================

@router.get("/tipos-documento", response_model=List[TipoDocumento])
def listar_tipos_documento(
    activo: bool = None,
    db: Session = Depends(get_db)
):
    """Listar tipos de documento tributario (endpoint público)."""
    query = db.query(TipoDocumentoModel)
    
    if activo is not None:
        query = query.filter(TipoDocumentoModel.activo == activo)
    
    tipos = query.order_by(TipoDocumentoModel.nombre).all()
    return tipos


# ============================================
# PRODUCTOS DE CARNES (Para WMS)
# ============================================

@router.get("/productos-carnes", response_model=List[Dict])
def listar_productos_carnes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Listar productos de la categoría CARNES para el sistema WMS (filtrado por tenant)."""
    from database.models import Producto, CategoriaProducto
    
    # Buscar categoría CARNES
    categoria_carnes = db.query(CategoriaProducto).filter(
        CategoriaProducto.nombre.ilike('CARNES')
    ).first()
    
    if not categoria_carnes:
        return []
    
    # Obtener productos de carnes filtrado por tenant
    productos = db.query(Producto).filter(
        Producto.categoria_id == categoria_carnes.id,
        Producto.tenant_id == current_user.tenant_id
    ).all()
    
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "sku": p.sku,
            "descripcion": p.descripcion or ""
        }
        for p in productos
    ]


# ============================================
# ENDPOINTS DE CARGA INICIAL
# ============================================

@router.post("/seed/all")
def seed_all_maestras(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Cargar datos iniciales para todas las tablas maestras.
    Solo ejecuta si las tablas están vacías.
    """
    result = {
        "status": "success",
        "loaded": [],
        "skipped": [],
        "errors": []
    }
    
    try:
        # 1. Categorías de producto
        if db.query(CategoriaProductoModel).count() == 0:
            categorias = [
                {"nombre": "Panificados", "descripcion": "Productos de panadería"},
                {"nombre": "Lácteos", "descripcion": "Productos lácteos"},
                {"nombre": "Carnes", "descripcion": "Productos cárnicos"},
                {"nombre": "Verduras", "descripcion": "Productos vegetales"},
                {"nombre": "Frutas", "descripcion": "Productos frutales"},
                {"nombre": "Bebidas", "descripcion": "Bebidas y líquidos"},
                {"nombre": "Snacks", "descripcion": "Aperitivos y snacks"},
                {"nombre": "Abarrotes", "descripcion": "Productos de abarrotes"}
            ]
            
            for cat_data in categorias:
                categoria = CategoriaProductoModel(**cat_data)
                db.add(categoria)
            
            db.commit()
            result["loaded"].append(f"Categorías: {len(categorias)} items")
        else:
            result["skipped"].append("Categorías (ya existen)")
        
        # 2. Tipos de documento
        if db.query(TipoDocumentoModel).count() == 0:
            tipos_doc = [
                {"codigo": "BOL", "nombre": "Boleta", "descripcion": "Boleta de venta"},
                {"codigo": "FAC", "nombre": "Factura", "descripcion": "Factura de venta"},
                {"codigo": "NC", "nombre": "Nota de Crédito", "descripcion": "Nota de crédito"},
                {"codigo": "ND", "nombre": "Nota de Débito", "descripcion": "Nota de débito"}
            ]
            
            for doc_data in tipos_doc:
                tipo_doc = TipoDocumentoModel(**doc_data)
                db.add(tipo_doc)
            
            db.commit()
            result["loaded"].append(f"Tipos de documento: {len(tipos_doc)} items")
        else:
            result["skipped"].append("Tipos de documento (ya existen)")
        
        # 3. Unidades de medida
        if db.query(UnidadMedidaModel).count() == 0:
            unidades = [
                {"nombre": "Kilogramo", "simbolo": "kg", "factor": 1.0},
                {"nombre": "Gramo", "simbolo": "g", "factor": 0.001},
                {"nombre": "Unidad", "simbolo": "un", "factor": 1.0},
                {"nombre": "Litro", "simbolo": "l", "factor": 1.0},
                {"nombre": "Metro", "simbolo": "m", "factor": 1.0},
                {"nombre": "Caja", "simbolo": "caja", "factor": 1.0},
                {"nombre": "Bolsa", "simbolo": "bolsa", "factor": 1.0}
            ]
            
            for unidad_data in unidades:
                unidad = UnidadMedidaModel(**unidad_data)
                db.add(unidad)
            
            db.commit()
            result["loaded"].append(f"Unidades de medida: {len(unidades)} items")
        else:
            result["skipped"].append("Unidades de medida (ya existen)")
        
        # 4. Medios de pago
        if db.query(MedioPagoModel).count() == 0:
            medios_pago = [
                {"nombre": "Efectivo", "activo": True},
                {"nombre": "Tarjeta de Débito", "activo": True},
                {"nombre": "Tarjeta de Crédito", "activo": True},
                {"nombre": "Transferencia", "activo": True},
                {"nombre": "Cheque", "activo": True},
                {"nombre": "MercadoPago", "activo": True}
            ]
            
            for pago_data in medios_pago:
                medio_pago = MedioPagoModel(**pago_data)
                db.add(medio_pago)
            
            db.commit()
            result["loaded"].append(f"Medios de pago: {len(medios_pago)} items")
        else:
            result["skipped"].append("Medios de pago (ya existen)")
        
        # 5. Estados de cheque
        if db.query(EstadoChequeModel).count() == 0:
            estados_cheque = [
                {"nombre": "Recibido", "descripcion": "Cheque recibido"},
                {"nombre": "Depositado", "descripcion": "Cheque depositado"},
                {"nombre": "Cobrado", "descripcion": "Cheque cobrado"},
                {"nombre": "Rebotado", "descripcion": "Cheque rebotado"},
                {"nombre": "Cancelado", "descripcion": "Cheque cancelado"}
            ]
            
            for estado_data in estados_cheque:
                estado = EstadoChequeModel(**estado_data)
                db.add(estado)
            
            db.commit()
            result["loaded"].append(f"Estados de cheque: {len(estados_cheque)} items")
        else:
            result["skipped"].append("Estados de cheque (ya existen)")
        
        # 6. Bancos
        if db.query(BancoModel).count() == 0:
            bancos = [
                {"nombre": "Banco de Chile", "codigo": "001"},
                {"nombre": "Banco Santander", "codigo": "037"},
                {"nombre": "Banco Estado", "codigo": "012"},
                {"nombre": "Banco BCI", "codigo": "009"},
                {"nombre": "Banco Falabella", "codigo": "051"},
                {"nombre": "Banco Itaú", "codigo": "039"},
                {"nombre": "Banco Security", "codigo": "049"}
            ]
            
            for banco_data in bancos:
                banco = BancoModel(**banco_data)
                db.add(banco)
            
            db.commit()
            result["loaded"].append(f"Bancos: {len(bancos)} items")
        else:
            result["skipped"].append("Bancos (ya existen)")
        
        # 7. Tipos de venta
        if db.query(TipoVentaModel).count() == 0:
            tipos_venta = [
                {"nombre": "Unitario", "descripcion": "Venta por unidades"},
                {"nombre": "Por Peso", "descripcion": "Venta por peso en kg"}
            ]
            
            for tipo_data in tipos_venta:
                tipo_venta = TipoVentaModel(**tipo_data)
                db.add(tipo_venta)
            
            db.commit()
            result["loaded"].append(f"Tipos de venta: {len(tipos_venta)} items")
        else:
            result["skipped"].append("Tipos de venta (ya existen)")
        
    except Exception as e:
        db.rollback()
        result["status"] = "error"
        result["errors"].append(str(e))
    
    return result


@router.get("/seed/status")
def get_seed_status(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Verificar estado de las tablas maestras.
    """
    return {
        "categorias": db.query(CategoriaProductoModel).count(),
        "tipos_documento": db.query(TipoDocumentoModel).count(),
        "unidades_medida": db.query(UnidadMedidaModel).count(),
        "medios_pago": db.query(MedioPagoModel).count(),
        "estados_cheque": db.query(EstadoChequeModel).count(),
        "bancos": db.query(BancoModel).count(),
        "tipos_venta": db.query(TipoVentaModel).count()
    }
