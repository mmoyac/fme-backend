"""
Router para el sistema de enrolamiento de vehículos y trazabilidad de lotes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database.database import get_db
from database.models import (
    Enrolamiento as EnrolamientoModel,
    Lote as LoteModel,
    Proveedor as ProveedorModel,
    TipoProveedor as TipoProveedorModel,
    User,
    Producto as ProductoModel,
    StockCajasProveedor as StockCajasProveedorModel,
    MovimientoStockCajas as MovimientoStockCajasModel
)
from schemas.enrolamiento import (
    EnrolamientoCreate, EnrolamientoUpdate, EnrolamientoResponse, EnrolamientoList,
    LoteCreate, LoteUpdate, LoteResponse, LoteList,
    FiltroEnrolamiento, FiltroLote, EstadisticasEnrolamiento, ProveedoresCarne
)
from routers.auth import get_current_active_user

router = APIRouter()


# Dependencia para verificar permisos
def get_current_user_with_wms_access(current_user: User = Depends(get_current_active_user)):
    """Solo usuarios admin o con permisos WMS pueden acceder."""
    if current_user.role.nombre not in ["admin", "bodeguero", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de bodega o administrador"
        )
    return current_user


# ============================================
# PROVEEDORES FILTRADOS (SOLO CARNES)
# ============================================

@router.get("/proveedores-carne", response_model=List[ProveedoresCarne])
def listar_proveedores_carne(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar solo los proveedores de tipo CARNES para enrolamiento."""
    return (
        db.query(ProveedorModel)
        .join(TipoProveedorModel)
        .filter(
            TipoProveedorModel.codigo == "CARNES",
            ProveedorModel.activo == True,
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .all()
    )


# ============================================
# ENROLAMIENTOS
# ============================================

@router.get("/enrolamientos", response_model=List[EnrolamientoList])
def listar_enrolamientos(
    filtro: FiltroEnrolamiento = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Listar enrolamientos con filtros opcionales."""
    query = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(ProveedorModel.tenant_id == current_user.tenant_id)
        .options(
            joinedload(EnrolamientoModel.tipo_vehiculo),
            joinedload(EnrolamientoModel.proveedor),
            joinedload(EnrolamientoModel.estado),
            joinedload(EnrolamientoModel.usuario_registro)
        )
    )
    
    # Aplicar filtros
    if filtro.estado_id:
        query = query.filter(EnrolamientoModel.estado_id == filtro.estado_id)
    if filtro.proveedor_id:
        query = query.filter(EnrolamientoModel.proveedor_id == filtro.proveedor_id)
    if filtro.tipo_vehiculo_id:
        query = query.filter(EnrolamientoModel.tipo_vehiculo_id == filtro.tipo_vehiculo_id)
    if filtro.fecha_desde:
        query = query.filter(EnrolamientoModel.fecha_inicio >= filtro.fecha_desde)
    if filtro.fecha_hasta:
        query = query.filter(EnrolamientoModel.fecha_inicio <= filtro.fecha_hasta)
    if filtro.patente:
        query = query.filter(EnrolamientoModel.patente.ilike(f"%{filtro.patente}%"))
    if filtro.numero_documento:
        query = query.filter(EnrolamientoModel.numero_documento.ilike(f"%{filtro.numero_documento}%"))
    
    # Ordenar por fecha más reciente
    query = query.order_by(EnrolamientoModel.fecha_inicio.desc())
    
    # Paginación
    enrolamientos = query.offset(skip).limit(limit).all()
    
    # Transformar a lista plana
    resultado = []
    for enr in enrolamientos:
        resultado.append({
            "id": enr.id,
            "patente": enr.patente,
            "chofer": enr.chofer,
            "numero_documento": enr.numero_documento,
            "fecha_inicio": enr.fecha_inicio,
            "fecha_termino": enr.fecha_termino,
            "tipo_vehiculo_nombre": enr.tipo_vehiculo.nombre,
            "proveedor_nombre": enr.proveedor.nombre,
            "estado_nombre": enr.estado.nombre,
            "usuario_registro_nombre": enr.usuario_registro.nombre_completo
        })
    
    return resultado


@router.get("/enrolamientos/{enrolamiento_id}", response_model=EnrolamientoResponse)
def obtener_enrolamiento(
    enrolamiento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Obtener un enrolamiento específico con todos sus detalles."""
    enrolamiento = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(
            EnrolamientoModel.id == enrolamiento_id,
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .options(
            joinedload(EnrolamientoModel.tipo_vehiculo),
            joinedload(EnrolamientoModel.proveedor),
            joinedload(EnrolamientoModel.estado),
            joinedload(EnrolamientoModel.usuario_registro)
        )
        .first()
    )
    
    if not enrolamiento:
        raise HTTPException(status_code=404, detail="Enrolamiento no encontrado")
    
    return enrolamiento


@router.post("/enrolamientos", response_model=EnrolamientoResponse, status_code=status.HTTP_201_CREATED)
def crear_enrolamiento(
    enrolamiento: EnrolamientoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Crear un nuevo enrolamiento de vehículo."""
    # Verificar que el proveedor es de tipo CARNES y pertenece al tenant
    proveedor = (
        db.query(ProveedorModel)
        .join(TipoProveedorModel)
        .filter(
            ProveedorModel.id == enrolamiento.proveedor_id,
            TipoProveedorModel.codigo == "CARNES",
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not proveedor:
        raise HTTPException(
            status_code=400,
            detail="El proveedor debe ser de tipo CARNES y pertenecer a su organización"
        )
    
    # Crear el enrolamiento
    db_enrolamiento = EnrolamientoModel(**enrolamiento.model_dump())
    db.add(db_enrolamiento)
    db.commit()
    db.refresh(db_enrolamiento)
    
    # Recargar con todas las relaciones necesarias
    enrolamiento_completo = (
        db.query(EnrolamientoModel)
        .options(
            joinedload(EnrolamientoModel.tipo_vehiculo),
            joinedload(EnrolamientoModel.proveedor),
            joinedload(EnrolamientoModel.estado),
            joinedload(EnrolamientoModel.usuario_registro)
        )
        .filter(EnrolamientoModel.id == db_enrolamiento.id)
        .first()
    )
    
    return enrolamiento_completo


@router.put("/enrolamientos/{enrolamiento_id}", response_model=EnrolamientoResponse)
def actualizar_enrolamiento(
    enrolamiento_id: int,
    enrolamiento: EnrolamientoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Actualizar un enrolamiento (cambio de estado, fecha término, etc)."""
    db_enrolamiento = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(
            EnrolamientoModel.id == enrolamiento_id,
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not db_enrolamiento:
        raise HTTPException(status_code=404, detail="Enrolamiento no encontrado")
    
    # Si se está finalizando (estado FINALIZADO), poner fecha de término
    if enrolamiento.estado_id:
        from database.models import EstadoEnrolamiento as EstadoEnrolamientoModel
        nuevo_estado = db.query(EstadoEnrolamientoModel).filter(EstadoEnrolamientoModel.id == enrolamiento.estado_id).first()
        if nuevo_estado and nuevo_estado.codigo == "FINALIZADO":
            # Cuando se finaliza, activar disponibilidad de todos los lotes
            for lote in db_enrolamiento.lotes:
                lote.disponible_venta = True
            
            # Si no se proporciona fecha_termino, usar la actual
            if not enrolamiento.fecha_termino:
                enrolamiento.fecha_termino = datetime.now()
            
            # ACTUALIZAR STOCK DE CAJAS POR PROVEEDOR
            actualizar_stock_cajas_desde_enrolamiento(db, db_enrolamiento, current_user)
    
    # Actualizar solo los campos proporcionados
    update_data = enrolamiento.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_enrolamiento, field, value)
    
    db.commit()
    db.refresh(db_enrolamiento)
    
    # Recargar con todas las relaciones necesarias
    enrolamiento_completo = (
        db.query(EnrolamientoModel)
        .options(
            joinedload(EnrolamientoModel.tipo_vehiculo),
            joinedload(EnrolamientoModel.proveedor),
            joinedload(EnrolamientoModel.estado),
            joinedload(EnrolamientoModel.usuario_registro)
        )
        .filter(EnrolamientoModel.id == db_enrolamiento.id)
        .first()
    )
    
    return enrolamiento_completo


@router.delete("/enrolamientos/{enrolamiento_id}")
def eliminar_enrolamiento(
    enrolamiento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Eliminar un enrolamiento (solo si no tiene lotes asociados)."""
    db_enrolamiento = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(
            EnrolamientoModel.id == enrolamiento_id,
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not db_enrolamiento:
        raise HTTPException(status_code=404, detail="Enrolamiento no encontrado")
    
    # Verificar que no tenga lotes
    if db_enrolamiento.lotes:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el enrolamiento porque tiene {len(db_enrolamiento.lotes)} lotes asociados"
        )
    
    db.delete(db_enrolamiento)
    db.commit()
    return None


# ============================================
# LOTES INDIVIDUALES
# ============================================

@router.get("/lotes", response_model=List[LoteList])
def listar_lotes(
    filtro: FiltroLote = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Listar lotes con filtros opcionales."""
    query = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(ProductoModel.tenant_id == current_user.tenant_id)
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
    )
    
    # Aplicar filtros
    if filtro.enrolamiento_id:
        query = query.filter(LoteModel.enrolamiento_id == filtro.enrolamiento_id)
    if filtro.producto_id:
        query = query.filter(LoteModel.producto_id == filtro.producto_id)
    if filtro.ubicacion_id:
        query = query.filter(LoteModel.ubicacion_id == filtro.ubicacion_id)
    if filtro.disponible_venta is not None:
        query = query.filter(LoteModel.disponible_venta == filtro.disponible_venta)
    if filtro.vendido is not None:
        query = query.filter(LoteModel.vendido == filtro.vendido)
    if filtro.fecha_vencimiento_desde:
        query = query.filter(LoteModel.fecha_vencimiento >= filtro.fecha_vencimiento_desde)
    if filtro.fecha_vencimiento_hasta:
        query = query.filter(LoteModel.fecha_vencimiento <= filtro.fecha_vencimiento_hasta)
    
    # Ordenar por fecha de vencimiento (FIFO)
    query = query.order_by(LoteModel.fecha_vencimiento.asc())
    
    # Paginación
    lotes = query.offset(skip).limit(limit).all()
    
    # Transformar a lista plana
    resultado = []
    for lote in lotes:
        resultado.append({
            "id": lote.id,
            "codigo_lote": lote.codigo_lote,
            "qr_propio": lote.qr_propio,
            "peso_original": lote.peso_original,
            "peso_actual": lote.peso_actual,
            "fecha_vencimiento": lote.fecha_vencimiento,
            "disponible_venta": lote.disponible_venta,
            "vendido": lote.vendido,
            "fecha_registro": lote.fecha_registro,
            "producto_nombre": lote.producto.nombre,
            "ubicacion_codigo": lote.ubicacion.codigo,
            "enrolamiento_patente": lote.enrolamiento.patente
        })
    
    return resultado


@router.get("/lotes/{lote_id}", response_model=LoteResponse)
def obtener_lote(
    lote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Obtener un lote específico con todos sus detalles."""
    lote = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.id == lote_id,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
        .first()
    )
    
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    return lote


@router.post("/lotes", response_model=LoteResponse, status_code=status.HTTP_201_CREATED)
def crear_lote(
    lote: LoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Crear un nuevo lote individual."""
    # Verificar código único dentro del tenant
    existing_lote = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.codigo_lote == lote.codigo_lote,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if existing_lote:
        raise HTTPException(status_code=400, detail="Ya existe un lote con este código")
    
    # Verificar QR único dentro del tenant
    existing_qr = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.qr_propio == lote.qr_propio,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if existing_qr:
        raise HTTPException(status_code=400, detail="Ya existe un lote con este QR")
    
    # Verificar que el producto pertenece al tenant
    producto = (
        db.query(ProductoModel)
        .filter(
            ProductoModel.id == lote.producto_id,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # El lote se marca como disponible solo si el enrolamiento está FINALIZADO
    enrolamiento = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(
            EnrolamientoModel.id == lote.enrolamiento_id,
            ProveedorModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    disponible_venta = False
    if enrolamiento and enrolamiento.estado.codigo == "FINALIZADO":
        disponible_venta = True
    
    db_lote = LoteModel(**lote.model_dump(), disponible_venta=disponible_venta)
    db.add(db_lote)
    db.commit()
    db.refresh(db_lote)
    
    # Recargar con todas las relaciones necesarias
    lote_completo = (
        db.query(LoteModel)
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
        .filter(LoteModel.id == db_lote.id)
        .first()
    )
    
    return lote_completo


@router.put("/lotes/{lote_id}", response_model=LoteResponse)
def actualizar_lote(
    lote_id: int,
    lote: LoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Actualizar un lote (peso, ubicación, estado, etc)."""
    db_lote = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.id == lote_id,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not db_lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    # Actualizar solo los campos proporcionados
    update_data = lote.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_lote, field, value)
    
    db.commit()
    db.refresh(db_lote)
    
    # Recargar con todas las relaciones necesarias
    lote_completo = (
        db.query(LoteModel)
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
        .filter(LoteModel.id == db_lote.id)
        .first()
    )
    
    return lote_completo


@router.delete("/lotes/{lote_id}")
def eliminar_lote(
    lote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Eliminar un lote (solo si no está vendido)."""
    db_lote = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.id == lote_id,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not db_lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    # Verificar que no esté vendido
    if db_lote.vendido:
        raise HTTPException(status_code=400, detail="No se puede eliminar un lote vendido")
    
    db.delete(db_lote)
    db.commit()
    
    return {"message": "Lote eliminado exitosamente"}


@router.get("/lotes/{lote_id}/etiqueta/pdf")
def generar_etiqueta_pdf(
    lote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Generar etiqueta PDF para un lote específico."""
    from fastapi.responses import FileResponse
    import qrcode
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import mm
    from io import BytesIO
    import tempfile
    import os
    
    # Obtener el lote con relaciones
    lote = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.id == lote_id,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
        .first()
    )
    
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        temp_path = tmp_file.name
    
    try:
        # Crear PDF
        c = canvas.Canvas(temp_path, pagesize=(80*mm, 60*mm))  # Etiqueta pequeña
        
        # Título
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5*mm, 50*mm, f"LOTE: {lote.codigo_lote}")
        
        # Información del producto
        c.setFont("Helvetica", 8)
        c.drawString(5*mm, 45*mm, f"Producto: {lote.producto.nombre}")
        c.drawString(5*mm, 41*mm, f"Peso: {lote.peso_actual} kg")
        c.drawString(5*mm, 37*mm, f"Venc: {lote.fecha_vencimiento.strftime('%d/%m/%Y')}")
        c.drawString(5*mm, 33*mm, f"Ubicación: {lote.ubicacion.codigo}")
        
        # Información de trazabilidad original
        if lote.qr_original:
            c.drawString(5*mm, 29*mm, f"QR Orig: {lote.qr_original}")
        if lote.lote_proveedor:
            c.drawString(5*mm, 25*mm, f"Lote Prov: {lote.lote_proveedor}")
        
        # QR Code (ajustar posición si hay más información)
        qr_y_position = 15*mm if (lote.qr_original or lote.lote_proveedor) else 25*mm
        qr_img = qrcode.make(lote.qr_propio)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Guardar QR temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as qr_tmp:
            qr_tmp.write(qr_buffer.getvalue())
            qr_path = qr_tmp.name
        
        # Insertar QR en PDF
        c.drawImage(qr_path, 45*mm, qr_y_position, width=25*mm, height=25*mm)
        
        c.save()
        
        # Limpiar QR temporal
        os.unlink(qr_path)
        
        return FileResponse(
            temp_path,
            media_type='application/pdf',
            filename=f'etiqueta_lote_{lote.codigo_lote}.pdf'
        )
    
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Error generando etiqueta: {str(e)}")


@router.post("/lotes/etiquetas/pdf")
def generar_etiquetas_multiples_pdf(
    lote_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_wms_access)
):
    """Generar etiquetas PDF para múltiples lotes."""
    from fastapi.responses import FileResponse
    import qrcode
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from io import BytesIO
    import tempfile
    import os
    
    if not lote_ids:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un lote")
    
    # Obtener lotes
    lotes = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.id.in_(lote_ids),
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .options(
            joinedload(LoteModel.producto),
            joinedload(LoteModel.ubicacion),
            joinedload(LoteModel.enrolamiento)
        )
        .all()
    )
    
    if not lotes:
        raise HTTPException(status_code=404, detail="No se encontraron lotes")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        temp_path = tmp_file.name
    
    try:
        # Crear PDF con múltiples etiquetas
        c = canvas.Canvas(temp_path, pagesize=A4)
        page_width, page_height = A4
        
        etiqueta_width = 80*mm
        etiqueta_height = 60*mm
        margen = 10*mm
        
        # Calcular cuántas etiquetas caben por fila y columna
        etiquetas_por_fila = int((page_width - 2*margen) // etiqueta_width)
        etiquetas_por_columna = int((page_height - 2*margen) // etiqueta_height)
        
        x_pos = margen
        y_pos = page_height - margen - etiqueta_height
        etiquetas_en_pagina = 0
        
        for lote in lotes:
            # Si se acabó el espacio en la página, crear nueva página
            if etiquetas_en_pagina >= etiquetas_por_fila * etiquetas_por_columna:
                c.showPage()
                x_pos = margen
                y_pos = page_height - margen - etiqueta_height
                etiquetas_en_pagina = 0
            
            # Dibujar etiqueta
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_pos + 5*mm, y_pos + 50*mm, f"LOTE: {lote.codigo_lote}")
            
            c.setFont("Helvetica", 8)
            c.drawString(x_pos + 5*mm, y_pos + 45*mm, f"Producto: {lote.producto.nombre}")
            c.drawString(x_pos + 5*mm, y_pos + 41*mm, f"Peso: {lote.peso_actual} kg")
            c.drawString(x_pos + 5*mm, y_pos + 37*mm, f"Venc: {lote.fecha_vencimiento.strftime('%d/%m/%Y')}")
            c.drawString(x_pos + 5*mm, y_pos + 33*mm, f"Ubicación: {lote.ubicacion.codigo}")
            
            # Información de trazabilidad original
            info_lines = 33
            if lote.qr_original:
                info_lines -= 4
                c.drawString(x_pos + 5*mm, y_pos + info_lines*mm, f"QR Orig: {lote.qr_original}")
            if lote.lote_proveedor:
                info_lines -= 4
                c.drawString(x_pos + 5*mm, y_pos + info_lines*mm, f"Lote Prov: {lote.lote_proveedor}")
            
            # QR Code (ajustar posición según información disponible)
            qr_y_pos = y_pos + max(15*mm, info_lines*mm - 8*mm)
            
            # QR Code
            qr_img = qrcode.make(lote.qr_propio)
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Guardar QR temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as qr_tmp:
                qr_tmp.write(qr_buffer.getvalue())
                qr_path = qr_tmp.name
            
            # Insertar QR en PDF
            c.drawImage(qr_path, x_pos + 45*mm, qr_y_pos, width=25*mm, height=25*mm)
            
            # Limpiar QR temporal
            os.unlink(qr_path)
            
            # Calcular siguiente posición
            x_pos += etiqueta_width
            if x_pos + etiqueta_width > page_width - margen:
                x_pos = margen
                y_pos -= etiqueta_height
            
            etiquetas_en_pagina += 1
        
        c.save()
        
        return FileResponse(
            temp_path,
            media_type='application/pdf',
            filename=f'etiquetas_lotes_{len(lotes)}_items.pdf'
        )
    
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Error generando etiquetas: {str(e)}")


# ============================================
# ESTADÍSTICAS
# ============================================

@router.get("/estadisticas", response_model=EstadisticasEnrolamiento)
def obtener_estadisticas_enrolamiento(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estadísticas generales del sistema de enrolamiento."""
    from database.models import EstadoEnrolamiento as EstadoEnrolamientoModel
    from sqlalchemy import func
    
    # Total enrolamientos del tenant
    total_enrolamientos = (
        db.query(EnrolamientoModel)
        .join(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(ProveedorModel.tenant_id == current_user.tenant_id)
        .count()
    )
    
    # Contar por estado (solo del tenant)
    estados = (
        db.query(EstadoEnrolamientoModel.codigo, func.count(EnrolamientoModel.id))
        .outerjoin(EnrolamientoModel)
        .outerjoin(ProveedorModel, EnrolamientoModel.proveedor_id == ProveedorModel.id)
        .filter(
            (ProveedorModel.tenant_id == current_user.tenant_id) | (EnrolamientoModel.id == None)
        )
        .group_by(EstadoEnrolamientoModel.codigo)
        .all()
    )
    
    estados_dict = {estado: count for estado, count in estados}
    
    # Estadísticas de lotes (solo del tenant)
    total_lotes = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(ProductoModel.tenant_id == current_user.tenant_id)
        .count()
    )
    lotes_disponibles = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.disponible_venta == True,
            LoteModel.vendido == False,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .count()
    )
    lotes_vendidos = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.vendido == True,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .count()
    )
    
    # Cajas del mes actual (solo del tenant)
    from datetime import datetime
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cajas_por_mes = (
        db.query(LoteModel)
        .join(ProductoModel, LoteModel.producto_id == ProductoModel.id)
        .filter(
            LoteModel.fecha_registro >= inicio_mes,
            ProductoModel.tenant_id == current_user.tenant_id
        )
        .count()
    )
    
    return EstadisticasEnrolamiento(
        total_enrolamientos=total_enrolamientos,
        pendientes=estados_dict.get("PENDIENTE", 0),
        en_proceso=estados_dict.get("EN_PROCESO", 0),
        finalizados=estados_dict.get("FINALIZADO", 0),
        total_lotes=total_lotes,
        lotes_disponibles=lotes_disponibles,
        lotes_vendidos=lotes_vendidos,
        cajas_por_mes=cajas_por_mes
    )


def actualizar_stock_cajas_desde_enrolamiento(db: Session, db_enrolamiento, current_user):
    """
    Actualiza el stock de cajas basado en los datos del enrolamiento finalizado.
    
    - Recorre los lotes del enrolamiento
    - Identifica productos que son cajas de carnes
    - Actualiza el stock por proveedor usando el servicio de stock
    """
    print(f"📦 Iniciando actualización de stock desde enrolamiento {db_enrolamiento.id}")
    
    # Obtener lotes del enrolamiento
    lotes = (
        db.query(LoteModel)
        .filter(LoteModel.enrolamiento_id == db_enrolamiento.id)
        .all()
    )
    
    print(f"📋 Encontrados {len(lotes)} lotes en el enrolamiento")
    
    # Diccionario para agrupar por proveedor y producto
    cajas_por_proveedor_producto = {}
    
    for lote in lotes:
        # Obtener el producto del lote
        producto = (
            db.query(ProductoModel)
            .filter(ProductoModel.id == lote.producto_id)
            .first()
        )
        
        if not producto:
            print(f"⚠️  Producto no encontrado para lote {lote.id}")
            continue
            
        # Verificar si es un producto de carne
        if not producto.categoria or producto.categoria.nombre != "CARNES":
            categoria_nombre = producto.categoria.nombre if producto.categoria else "Sin categoría"
            print(f"🚫 Producto {producto.nombre} no es de categoría CARNES (categoria: {categoria_nombre}), saltando")
            continue
            
        # Obtener el proveedor del enrolamiento
        proveedor_id = db_enrolamiento.proveedor_id
        
        if not proveedor_id:
            print("⚠️  Enrolamiento sin proveedor asignado")
            continue
            
        # Clave única: proveedor + producto
        clave = (proveedor_id, lote.producto_id)
        
        if clave not in cajas_por_proveedor_producto:
            cajas_por_proveedor_producto[clave] = {
                'proveedor_id': proveedor_id,
                'producto_id': lote.producto_id,
                'producto_nombre': producto.nombre,
                'cantidad_cajas': 0
            }
            
        # Cada lote representa una caja
        cajas_por_proveedor_producto[clave]['cantidad_cajas'] += 1
        
        print(f"✅ Agregando 1 caja de {producto.nombre} (lote {lote.codigo_lote})")
    
    # Ahora actualizar el stock para cada combinación proveedor-producto
    total_actualizaciones = 0
    
    for info in cajas_por_proveedor_producto.values():
        if info['cantidad_cajas'] <= 0:
            continue
            
        proveedor_id = info['proveedor_id']
        producto_id = info['producto_id']
        cantidad = info['cantidad_cajas']
        
        print(f"🔄 Actualizando stock: {cantidad} cajas de {info['producto_nombre']}")
        
        # Buscar o crear el registro de stock
        stock_existente = (
            db.query(StockCajasProveedorModel)
            .filter(
                StockCajasProveedorModel.proveedor_id == proveedor_id,
                StockCajasProveedorModel.producto_id == producto_id
            )
            .first()
        )
        
        if stock_existente:
            # Actualizar stock existente
            stock_anterior = stock_existente.cajas_disponibles
            stock_existente.cajas_disponibles += cantidad
            stock_existente.cajas_totales_recibidas += cantidad
            stock_existente.fecha_ultima_actualizacion = datetime.now()
            
            print(f"📈 Stock actualizado: {stock_anterior} → {stock_existente.cajas_disponibles}")
        else:
            # Crear nuevo registro de stock
            nuevo_stock = StockCajasProveedorModel(
                proveedor_id=proveedor_id,
                producto_id=producto_id,
                cajas_disponibles=cantidad,
                cajas_totales_recibidas=cantidad,
                cajas_totales_vendidas=0,
                fecha_ultima_actualizacion=datetime.now()
            )
            
            db.add(nuevo_stock)
            print(f"🆕 Nuevo stock creado: {cantidad} cajas")
        
        # Crear movimiento de stock
        stock_despues = stock_existente.cajas_disponibles if stock_existente else cantidad
        stock_antes = stock_despues - cantidad
        
        movimiento = MovimientoStockCajasModel(
            proveedor_id=proveedor_id,
            producto_id=producto_id,
            tipo_movimiento="ENTRADA_ENROLAMIENTO",
            cajas_movimiento=cantidad,
            cajas_antes=stock_antes,
            cajas_despues=stock_despues,
            descripcion=f"Stock agregado desde enrolamiento #{db_enrolamiento.id}",
            usuario="sistema",
            enrolamiento_id=db_enrolamiento.id,
            fecha_movimiento=datetime.now()
        )
        
        db.add(movimiento)
        total_actualizaciones += 1
    
    try:
        # Commit de todas las operaciones
        db.commit()
        print(f"✅ Stock actualizado exitosamente. {total_actualizaciones} productos actualizados")
        
    except Exception as e:
        print(f"❌ Error al actualizar stock: {str(e)}")
        db.rollback()
        raise