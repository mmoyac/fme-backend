"""
Router para endpoints de Precios.
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Precio, Producto, Local, CategoriaProducto, UnidadMedida
from utils.excel import generar_xlsx, FORMATO_CLP
from schemas.precio import PrecioResponse, PrecioCreate, PrecioUpdate
from routers.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[PrecioResponse])
def listar_precios(
    skip: int = 0,
    limit: int = 5000,
    producto_id: int = None,
    local_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista precios del tenant con filtros opcionales.
    
    **Uso:** Backoffice - Tabla de precios
    """
    # Unir con Producto para filtrar por tenant_id
    query = db.query(Precio).join(Producto).filter(Producto.tenant_id == current_user.tenant_id)
    
    if producto_id:
        query = query.filter(Precio.producto_id == producto_id)
    if local_id:
        query = query.filter(Precio.local_id == local_id)
    
    precios = query.offset(skip).limit(limit).all()
    return precios


@router.get("/excel")
def exportar_precios_excel(
    q: Optional[str] = None,
    local_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Exporta a Excel los precios del tenant con los mismos filtros de la pantalla de Precios
    (búsqueda por nombre/SKU, local y categoría). Los productos sin precio en el filtro
    aparecen igual, marcados "Sin precio". Pedido del cliente: reunión 16-11-26, punto 1.6.1.
    """
    productos_q = (
        db.query(Producto, CategoriaProducto.nombre)
        .outerjoin(CategoriaProducto, CategoriaProducto.id == Producto.categoria_id)
        .filter(Producto.tenant_id == current_user.tenant_id)
    )
    if q and q.strip():
        patron = f"%{q.strip()}%"
        productos_q = productos_q.filter(Producto.nombre.ilike(patron) | Producto.sku.ilike(patron))
    if categoria_id:
        productos_q = productos_q.filter(Producto.categoria_id == categoria_id)
    productos = productos_q.order_by(Producto.nombre).all()

    precios_q = (
        db.query(Precio, Local.nombre, UnidadMedida.nombre)
        .join(Local, Local.id == Precio.local_id)
        .join(UnidadMedida, UnidadMedida.id == Precio.unidad_medida_id)
        .filter(Precio.producto_id.in_([p.id for p, _ in productos] or [0]),
                Local.tenant_id == current_user.tenant_id)
    )
    if local_id:
        precios_q = precios_q.filter(Precio.local_id == local_id)
    por_producto = {}
    for precio, local_nombre, unidad_nombre in precios_q.order_by(Local.nombre, UnidadMedida.nombre).all():
        por_producto.setdefault(precio.producto_id, []).append((local_nombre, unidad_nombre, precio.monto_precio))

    filas = []
    for p, categoria in productos:
        incluye_iva = bool(p.precio_incluye_iva)
        lista = por_producto.get(p.id)
        if not lista:
            filas.append([p.sku, p.nombre, categoria, None, None, None, None, None, "Sin precio"])
            continue
        for local_nombre, unidad_nombre, monto in lista:
            monto = float(monto)
            neto = round(monto / 1.19, 2) if incluye_iva else monto
            filas.append([p.sku, p.nombre, categoria, local_nombre, unidad_nombre, monto,
                          "Sí" if incluye_iva else "No", neto, None if p.activo else "Producto inactivo"])

    contenido = generar_xlsx(
        "Precios",
        ["SKU", "Producto", "Categoría", "Local", "Unidad", "Precio", "Incluye IVA", "Precio neto", "Observación"],
        filas,
        anchos=[14, 38, 20, 18, 16, 12, 11, 13, 20],
        formatos={5: FORMATO_CLP, 7: FORMATO_CLP},
    )
    nombre = f"precios_{date.today().isoformat()}.xlsx"
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.post("/", response_model=PrecioResponse, status_code=status.HTTP_201_CREATED)
def crear_precio(precio: PrecioCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Crea un nuevo precio para un producto en un local del tenant.
    
    **Validaciones:**
    - Producto y local deben existir y pertenecer al tenant
    - No debe existir otro precio activo para el mismo producto/local
    
    **Uso:** Backoffice - Asignar precio
    """
    # Verificar que producto y local existan y pertenezcan al tenant
    producto = db.query(Producto).filter(Producto.id == precio.producto_id, Producto.tenant_id == current_user.tenant_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {precio.producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == precio.local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {precio.local_id} no encontrado"
        )
    
    # Verificar si ya existe un precio para este producto/local/unidad
    existing = db.query(Precio).filter(
        Precio.producto_id == precio.producto_id,
        Precio.local_id == precio.local_id,
        Precio.unidad_medida_id == precio.unidad_medida_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un precio para este producto/local/unidad. Use PUT para actualizar."
        )
    
    # Crear nuevo precio
    db_precio = Precio(**precio.model_dump())
    db.add(db_precio)
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.put("/{precio_id}", response_model=PrecioResponse)
def actualizar_precio(
    precio_id: int,
    precio: PrecioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un precio existente del tenant.
    
    **Uso:** Backoffice - Modificar precio
    """
    # Validar que el precio pertenece al tenant
    db_precio = db.query(Precio).join(Producto).filter(
        Precio.id == precio_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    # Actualizar campos
    if precio.monto_precio is not None:
        db_precio.monto_precio = precio.monto_precio
    if precio.unidad_medida_id is not None:
        db_precio.unidad_medida_id = precio.unidad_medida_id
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.put("/producto/{producto_id}/local/{local_id}/unidad/{unidad_medida_id}", response_model=PrecioResponse)
def actualizar_precio_por_producto_local(
    producto_id: int,
    local_id: int,
    unidad_medida_id: int,
    precio_data: PrecioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza o crea el precio de un producto en un local y unidad específicos del tenant.
    
    **Uso:** Backoffice - Asignar/actualizar precio por producto/local/unidad
    """
    # Verificar que producto y local existan y pertenezcan al tenant
    producto = db.query(Producto).filter(Producto.id == producto_id, Producto.tenant_id == current_user.tenant_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    local = db.query(Local).filter(Local.id == local_id, Local.tenant_id == current_user.tenant_id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {local_id} no encontrado"
        )
    
    # Buscar o crear precio
    db_precio = db.query(Precio).filter(
        Precio.producto_id == producto_id,
        Precio.local_id == local_id,
        Precio.unidad_medida_id == unidad_medida_id
    ).first()
    
    if db_precio:
        # Actualizar existente
        db_precio.monto_precio = precio_data.monto_precio
    else:
        # Crear nuevo
        db_precio = Precio(
            producto_id=producto_id,
            local_id=local_id,
            unidad_medida_id=unidad_medida_id,
            monto_precio=precio_data.monto_precio
        )
        db.add(db_precio)
    
    db.commit()
    db.refresh(db_precio)
    return db_precio


@router.get("/producto/{producto_id}/local/{local_id}", response_model=List[PrecioResponse])
def obtener_precios_producto_local(
    producto_id: int,
    local_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los precios de un producto en un local (por diferentes unidades de medida).
    
    **Uso:** Frontend/Backoffice - Para mostrar opciones de precio por unidad
    """
    precios = db.query(Precio).filter(
        Precio.producto_id == producto_id,
        Precio.local_id == local_id
    ).all()
    
    if not precios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existen precios para producto {producto_id} en local {local_id}"
        )
    
    return precios


@router.delete("/{precio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_precio(precio_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Elimina un precio del tenant.
    
    **Uso:** Backoffice - Eliminar precio
    """
    # Validar que el precio pertenece al tenant
    db_precio = db.query(Precio).join(Producto).filter(
        Precio.id == precio_id,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if not db_precio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Precio con ID {precio_id} no encontrado"
        )
    
    db.delete(db_precio)
    db.commit()
    return None
