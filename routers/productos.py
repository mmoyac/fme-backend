"""
Router para endpoints de Productos y Catálogo.
"""
from typing import List
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Producto, CategoriaProducto, MovimientoInventario, DetalleCompra, ItemPedido, IngredienteReceta, DetalleOrdenProduccion
from schemas.catalogo import ProductoCatalogo
from schemas.producto import ProductoResponse, ProductoCreate, ProductoUpdate
from services import inventario_service, tenant_service

from routers.auth import get_current_active_user

router = APIRouter()

# Directorio para guardar imágenes
UPLOAD_DIR = Path("static/productos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/catalogo", response_model=List[ProductoCatalogo])
def obtener_catalogo_web(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Obtiene el catálogo de productos con precios del local WEB.
    
    Detecta automáticamente el tenant por dominio:
    - masasestacion.cl → Productos de Masas Estación
    - elolivo.masasestacion.cl → Productos de El Olivo
    - localhost → Masas Estación (desarrollo)
    
    Retorna:
    - SKU del producto
    - Nombre del producto
    - Descripción del producto
    - Precio (del local WEB/e-commerce)
    - Stock total (suma de todos los locales físicos o WEB)
    
    **Ideal para:** Mostrar productos en la tienda online con precios de e-commerce
    """
    # Detectar y validar tenant
    tenant = tenant_service.get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    # Validar que el tenant esté activo
    tenant_service.validar_tenant_activo(tenant)
    
    catalogo = inventario_service.get_catalogo_web(db, tenant_id=tenant.id)
    return catalogo


@router.get("/catalogo/{sku}", response_model=ProductoCatalogo)
def obtener_producto_catalogo_por_sku(
    sku: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Obtiene un producto específico del catálogo web por SKU.
    Detecta automáticamente el tenant por dominio.
    Usado por las páginas de producto individual (para redes sociales).
    """
    tenant = tenant_service.get_tenant_from_request(request, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    tenant_service.validar_tenant_activo(tenant)

    catalogo = inventario_service.get_catalogo_web(db, tenant_id=tenant.id)
    producto = next((p for p in catalogo if p["sku"] == sku), None)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/catalogo-local/{local_id}")
def obtener_catalogo_local(
    local_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Obtiene el catálogo de productos con precios y stock de un local específico.
    
    **OPTIMIZADO para POS:** Devuelve TODO en una sola consulta SQL para evitar N+1 queries.
    
    Retorna para cada producto:
    - Datos básicos (id, sku, nombre, descripción, imagen_url)
    - Categoría (id, nombre, puntos_fidelidad)
    - Precio del local específico (precio_base en unidad mínima)
    - Stock del local específico
    - Unidad de medida
    
    **Uso:** POS / Backoffice - Crear pedidos desde local físico
    """
    from sqlalchemy import func
    from sqlalchemy.orm import joinedload
    from database.models import Precio, Inventario, UnidadMedida, CategoriaProducto
    
    # Query optimizada con JOINs para traer todo en una sola consulta
    query = (
        db.query(
            Producto.id,
            Producto.sku,
            Producto.nombre,
            Producto.descripcion,
            Producto.imagen_url,
            Producto.codigo_barra,
            Producto.categoria_id,
            Producto.tipo_producto_id,
            Producto.unidad_medida_id,
            Producto.es_vendible,
            Producto.activo,
            Producto.peso_bruto,
            CategoriaProducto.nombre.label('categoria_nombre'),
            CategoriaProducto.puntos_fidelidad.label('categoria_puntos'),
            Precio.monto_precio.label('precio_base'),
            Precio.unidad_medida_id.label('precio_unidad_medida_id'),
            Inventario.cantidad_stock.label('stock_local'),
            UnidadMedida.nombre.label('unidad_medida_nombre'),
            UnidadMedida.simbolo.label('unidad_medida_abrev'),
            UnidadMedida.factor_conversion
        )
        .outerjoin(CategoriaProducto, Producto.categoria_id == CategoriaProducto.id)
        .outerjoin(
            Precio,
            (Precio.producto_id == Producto.id) & (Precio.local_id == local_id)
        )
        .outerjoin(
            Inventario,
            (Inventario.producto_id == Producto.id) & (Inventario.local_id == local_id)
        )
        .outerjoin(
            UnidadMedida,
            UnidadMedida.id == Precio.unidad_medida_id
        )
        .filter(
            Producto.tenant_id == current_user.tenant_id,
            Producto.es_vendible == True,
            Producto.activo == True
        )
        .order_by(Producto.nombre)
        .all()
    )
    
    # Agrupar por producto (puede haber múltiples precios por unidad de medida)
    productos_dict = {}
    for row in query:
        producto_id = row.id
        
        if producto_id not in productos_dict:
            productos_dict[producto_id] = {
                'id': row.id,
                'sku': row.sku,
                'nombre': row.nombre,
                'descripcion': row.descripcion,
                'imagen_url': row.imagen_url,
                'codigo_barra': row.codigo_barra,
                'categoria_id': row.categoria_id,
                'categoria_nombre': row.categoria_nombre,
                'categoria_puntos_fidelidad': row.categoria_puntos or 0,
                'tipo_producto_id': row.tipo_producto_id,
                'unidad_medida_id': row.unidad_medida_id,
                'es_vendible': row.es_vendible,
                'activo': row.activo,
                'peso_bruto': float(row.peso_bruto) if row.peso_bruto is not None else None,
                'stock_local': row.stock_local or 0,
                'precios': []
            }
        
        # Agregar precio si existe (puede haber múltiples por unidad de medida)
        if row.precio_base is not None:
            productos_dict[producto_id]['precios'].append({
                'monto_precio': row.precio_base,
                'unidad_medida_id': row.precio_unidad_medida_id,
                'unidad_medida_nombre': row.unidad_medida_nombre,
                'unidad_medida_abrev': row.unidad_medida_abrev,
                'factor_conversion': row.factor_conversion or 1
            })
    
    # Encontrar precio base (menor factor de conversión) para cada producto
    result = []
    for producto in productos_dict.values():
        # Ordenar precios por factor de conversión (menor = unitario)
        if producto['precios']:
            precios_ordenados = sorted(
                producto['precios'],
                key=lambda p: p['factor_conversion']
            )
            precio_base = precios_ordenados[0]
            producto['precio_local'] = precio_base['monto_precio']
            producto['precio_unidad_medida'] = precio_base['unidad_medida_nombre']
        else:
            producto['precio_local'] = 0
            producto['precio_unidad_medida'] = None
        
        # Mantener todos los precios disponibles para el frontend
        # (útil si se quiere vender por otra unidad)
        result.append(producto)
    
    return result


# --------------------------------------------------
# CRUD Endpoints para Backoffice
# --------------------------------------------------

@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lista todos los productos con paginación (filtrados por tenant del usuario).
    
    **Uso:** Backoffice - Tabla de productos
    """
    from sqlalchemy.orm import joinedload
    from database.models import CategoriaProducto
    
    productos = (
        db.query(Producto)
        .options(
            joinedload(Producto.categoria).joinedload(CategoriaProducto.tipo_venta),
            joinedload(Producto.categoria)
        )
        .filter(Producto.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Preparar lista de respuesta con información de categoría
    result = []
    for p in productos:
        total_stock = sum(inv.cantidad_stock for inv in p.inventarios)
        # Obtener símbolo de unidad de medida
        unidad_medida_simbolo = p.unidad_medida.simbolo if p.unidad_medida else None
        # Crear diccionario con todos los campos base
        producto_dict = {
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'sku': p.sku,
            'imagen_url': p.imagen_url,
            'codigo_barra': p.codigo_barra,
            'categoria_id': p.categoria_id,
            'tipo_producto_id': p.tipo_producto_id,
            'unidad_medida_id': p.unidad_medida_id,
            'precio_compra': p.precio_compra,
            'costo_fabricacion': p.costo_fabricacion,
            'peso_bruto': p.peso_bruto,
            'es_vendible': p.es_vendible,
            'es_vendible_web': p.es_vendible_web,
            'es_ingrediente': p.es_ingrediente,
            'tiene_receta': p.tiene_receta,
            'activo': p.activo,
            'stock_minimo': p.stock_minimo,
            'stock_critico': p.stock_critico,
            'precio_incluye_iva': p.precio_incluye_iva,
            'descuento_contado': p.descuento_contado,
            'stock_actual': total_stock,
            # Información de categoría
            'categoria_nombre': p.categoria.nombre if p.categoria else None,
            'categoria_puntos_fidelidad': p.categoria.puntos_fidelidad if p.categoria else None,
            # Información de tipo de venta (peso vs cantidad)
            'tipo_venta_codigo': p.categoria.tipo_venta.codigo if p.categoria and p.categoria.tipo_venta else None,
            'tipo_venta_nombre': p.categoria.tipo_venta.nombre if p.categoria and p.categoria.tipo_venta else None,
            # Unidad de medida simbólica
            'unidad_medida_simbolo': unidad_medida_simbolo,
            # Unidad de compra (materias primas a granel)
            'unidad_compra_descripcion': p.unidad_compra_descripcion,
            'factor_conversion_compra': float(p.factor_conversion_compra) if p.factor_conversion_compra else 1,
        }
        result.append(producto_dict)
    return result


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Obtiene un producto por ID (filtrado por tenant del usuario).
    
    **Uso:** Backoffice - Detalle/Edición de producto
    """
    from sqlalchemy.orm import joinedload
    
    producto = (
        db.query(Producto)
        .options(
            joinedload(Producto.categoria).joinedload(CategoriaProducto.tipo_venta),
            joinedload(Producto.categoria)
        )
        .filter(
            Producto.id == producto_id,
            Producto.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Calcular stock actual
    total_stock = sum(inv.cantidad_stock for inv in producto.inventarios)
    # Obtener símbolo de unidad de medida
    unidad_medida_simbolo = producto.unidad_medida.simbolo if producto.unidad_medida else None
    # Retornar con información de categoría y unidad simbólica
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'sku': producto.sku,
        'imagen_url': producto.imagen_url,
        'codigo_barra': producto.codigo_barra,
        'categoria_id': producto.categoria_id,
        'tipo_producto_id': producto.tipo_producto_id,
        'unidad_medida_id': producto.unidad_medida_id,
        'precio_compra': producto.precio_compra,
        'costo_fabricacion': producto.costo_fabricacion,
        'peso_bruto': producto.peso_bruto,
        'es_vendible': producto.es_vendible,
        'es_vendible_web': producto.es_vendible_web,
        'es_ingrediente': producto.es_ingrediente,
        'tiene_receta': producto.tiene_receta,
        'activo': producto.activo,
        'stock_minimo': producto.stock_minimo,
        'stock_critico': producto.stock_critico,
        'precio_incluye_iva': producto.precio_incluye_iva,
        'descuento_contado': producto.descuento_contado,
        'stock_actual': total_stock,
        # Información de categoría
        'categoria_nombre': producto.categoria.nombre if producto.categoria else None,
        'categoria_puntos_fidelidad': producto.categoria.puntos_fidelidad if producto.categoria else None,
        # Información de tipo de venta (peso vs cantidad)
        'tipo_venta_codigo': producto.categoria.tipo_venta.codigo if producto.categoria and producto.categoria.tipo_venta else None,
        'tipo_venta_nombre': producto.categoria.tipo_venta.nombre if producto.categoria and producto.categoria.tipo_venta else None,
        # Unidad de medida simbólica
        'unidad_medida_simbolo': unidad_medida_simbolo,
        # Unidad de compra (materias primas a granel)
        'unidad_compra_descripcion': producto.unidad_compra_descripcion,
        'factor_conversion_compra': float(producto.factor_conversion_compra) if producto.factor_conversion_compra else 1,
    }


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Crea un nuevo producto.
    
    **Validaciones:**
    - SKU debe ser único
    
    **Uso:** Backoffice - Crear producto
    """
    # Verificar que el SKU no exista en el tenant
    existing = db.query(Producto).filter(
        Producto.sku == producto.sku,
        Producto.tenant_id == current_user.tenant_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"❌ SKU duplicado: Ya existe un producto con el código '{producto.sku}'. Por favor, usa un código diferente."
        )
    
    # Crear nuevo producto
    producto_data = producto.model_dump()
    producto_data['tenant_id'] = current_user.tenant_id
    db_producto = Producto(**producto_data)
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Stock inicial 0
    setattr(db_producto, "stock_actual", 0)
    
    return db_producto


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un producto existente.
    
    **Validaciones:**
    - Si se cambia el SKU, debe ser único
    
    **Uso:** Backoffice - Editar producto
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Si se está actualizando el SKU, verificar que sea único
    if producto.sku and producto.sku != db_producto.sku:
        existing = db.query(Producto).filter(Producto.sku == producto.sku).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con SKU '{producto.sku}'"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = producto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_producto, field, value)
    
    db.commit()
    db.refresh(db_producto)
    
    # Recalcular stock
    total_stock = sum(inv.cantidad_stock for inv in db_producto.inventarios)
    setattr(db_producto, "stock_actual", total_stock)
    
    return db_producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Elimina un producto.
    
    **Nota:** Esto también eliminará todos los registros relacionados:
    - Movimientos de inventario (historial)
    - Detalles de compras asociados
    - Inventario del producto en todos los locales
    - Precios del producto en todos los locales
    - Recetas, información nutricional, sellos (via cascade)
    
    **Uso:** Backoffice - Eliminar producto
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Eliminar dependencias que tienen RESTRICT en la FK
    
    # 1. Eliminar movimientos de inventario (historial)
    db.query(MovimientoInventario).filter(
        MovimientoInventario.producto_id == producto_id
    ).delete(synchronize_session=False)
    
    # 2. Eliminar detalles de compras
    db.query(DetalleCompra).filter(
        DetalleCompra.producto_id == producto_id
    ).delete(synchronize_session=False)
    
    # 3. Eliminar items de pedido (por si quedaron huérfanos)
    db.query(ItemPedido).filter(
        ItemPedido.producto_id == producto_id
    ).delete(synchronize_session=False)
    
    # 4. Eliminar referencias como ingrediente en recetas (usado_en_recetas)
    db.query(IngredienteReceta).filter(
        IngredienteReceta.producto_ingrediente_id == producto_id
    ).delete(synchronize_session=False)
    
    # 5. Eliminar detalles de órdenes de producción
    db.query(DetalleOrdenProduccion).filter(
        DetalleOrdenProduccion.producto_id == producto_id
    ).delete(synchronize_session=False)
    
    # 6. Ahora sí eliminar el producto (cascades se encargan del resto)
    db.delete(db_producto)
    db.commit()
    return None


@router.post("/{producto_id}/imagen", response_model=ProductoResponse)
async def subir_imagen_producto(
    producto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Sube una imagen para un producto.
    
    **Formatos permitidos:** JPG, JPEG, PNG, WEBP
    **Tamaño máximo:** 2MB
    
    **Uso:** Backoffice - Upload de imagen
    """
    # Verificar que el producto existe
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado"
        )
    
    # Validar formato de archivo
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Use: {', '.join(allowed_extensions)}"
        )
    
    # Validar tamaño (2MB)
    max_size = 2 * 1024 * 1024  # 2MB en bytes
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo excede el tamaño máximo de 2MB"
        )
    
    # Generar nombre de archivo único usando SKU
    filename = f"{db_producto.sku}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Guardar archivo
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Actualizar URL de imagen en base de datos
    db_producto.imagen_url = f"/static/productos/{filename}"
    db.commit()
    db.refresh(db_producto)
    
    return db_producto
