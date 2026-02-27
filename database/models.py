
"""
Modelos de la base de datos con SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, Text, Table, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from .database import Base
import enum

# --------------------------------------------------
# PALETAS DE COLORES (THEMES)
# --------------------------------------------------

class PaletaColores(Base):
    """
    Paletas de colores reutilizables para branding y temas visuales.
    Permite asociar una paleta a uno o varios tenants/configuraciones.
    """
    __tablename__ = "paleta_colores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    descripcion = Column(String(255), nullable=True)

    # Colores principales y avanzados (igual que en ConfiguracionLanding.colores)
    primario = Column(String(10), nullable=False)
    primario_light = Column(String(10), nullable=True)
    primario_dark = Column(String(10), nullable=True)
    secundario = Column(String(10), nullable=False)
    secundario_light = Column(String(10), nullable=True)
    secundario_dark = Column(String(10), nullable=True)
    acento = Column(String(10), nullable=True)
    fondo_hero_inicio = Column(String(10), nullable=True)
    fondo_hero_fin = Column(String(10), nullable=True)
    fondo_seccion = Column(String(10), nullable=True)

    es_publica = Column(Boolean, default=True, nullable=False)
    creado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones (opcional: si quieres asociar a tenants/configuraciones)
    # configuraciones = relationship("ConfiguracionLanding", back_populates="paleta_colores")


# --------------------------------------------------
# 0. MULTI-TENANT
# --------------------------------------------------

class Tenant(Base):
    """
    Tenants del sistema (Multi-tenant SaaS).
    Cada cliente tiene su propio tenant con configuración independiente.
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)  # 'masas-estacion', 'los-alpes'
    nombre = Column(String(100), nullable=False, index=True)  # 'Masas Estación'
    dominio_principal = Column(String(100), unique=True, nullable=True)  # 'masasestacion.cl'
    subdomain = Column(String(50), unique=True, nullable=True)  # 'masasestacion' para *.tuapp.cl
    activo = Column(Boolean, default=True, nullable=False)
    correlativo_pedido = Column(Integer, default=0, nullable=False)  # Correlativo para numero_pedido por tenant
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    configuracion_landing = relationship(
        "ConfiguracionLanding",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    productos = relationship("Producto", back_populates="tenant", passive_deletes=True)
    locales = relationship("Local", back_populates="tenant", passive_deletes=True)
    clientes = relationship("Cliente", back_populates="tenant", passive_deletes=True)
    pedidos = relationship("Pedido", back_populates="tenant", passive_deletes=True)
    usuarios = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    proveedores = relationship("Proveedor", back_populates="tenant", passive_deletes=True)


class ConfiguracionLanding(Base):
    """
    Configuración dinámica de la landing page por tenant (White-label).
    Permite personalizar colores, textos, logo y contenido sin cambiar código.
    """
    __tablename__ = "configuracion_landing"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Branding
    logo_url = Column(String(255), nullable=True)
    favicon_url = Column(String(255), nullable=True)
    nombre_comercial = Column(String(100), nullable=True)
    
    # Paleta de colores (FK opcional a tabla paleta_colores)
    paleta_id = Column(Integer, ForeignKey("paleta_colores.id", ondelete="SET NULL"), nullable=True)
    
    # Colores (JSON: {primario, secundario, fondo_hero_inicio, etc.})
    # NOTA: Si paleta_id está definido, estos colores se sobrescriben por los de la paleta
    colores = Column(JSON, nullable=False, server_default='{}')
    
    # Hero Section
    hero_titulo = Column(Text, nullable=True)
    hero_subtitulo = Column(Text, nullable=True)
    hero_imagen_url = Column(String(255), nullable=True)
    hero_cta_texto = Column(String(50), nullable=True)
    hero_cta_link = Column(String(100), nullable=True)
    hero_badges = Column(JSON, nullable=False, server_default='[]')  # [{icono, texto}]
    
    # Beneficios (JSON array: [{icono, titulo, descripcion}])
    beneficios = Column(JSON, nullable=False, server_default='[]')
    
    # Footer / Contacto
    redes_sociales = Column(JSON, nullable=False, server_default='{}')  # {facebook, instagram, whatsapp}
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    direccion = Column(Text, nullable=True)
    texto_footer_descripcion = Column(Text, nullable=True)
    texto_copyright = Column(String(200), nullable=True)
    
    # SEO Metadata
    meta_title = Column(String(100), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Configuración de visualización (E-commerce vs Catálogo)
    mostrar_precios = Column(Boolean, nullable=False, server_default='true')
    mostrar_stock = Column(Boolean, nullable=False, server_default='true')
    habilitar_carrito = Column(Boolean, nullable=False, server_default='true')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    tenant = relationship("Tenant", back_populates="configuracion_landing")
    paleta = relationship("PaletaColores", foreign_keys=[paleta_id])


# --------------------------------------------------
# 1. TABLAS MAESTRAS
# --------------------------------------------------

class TipoPedido(Base):
    """Tipos de pedido para distinguir manejo de inventario."""
    __tablename__ = "tipos_pedido"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)
    local_despacho_default_id = Column(Integer, ForeignKey("locales.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    pedidos = relationship("Pedido", back_populates="tipo_pedido")
    local_despacho_default = relationship("Local", foreign_keys=[local_despacho_default_id])


class TipoLocal(Base):
    """Tipos de locales: VENTA, FRIGORIFICO, etc."""
    __tablename__ = "tipos_local"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    locales = relationship("Local", back_populates="tipo_local")


class CategoriaProducto(Base):
    """Categorías de productos para clasificación y puntos de fidelidad."""
    __tablename__ = "categorias_producto"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String)
    puntos_fidelidad = Column(Integer, default=0)
    tipo_venta_id = Column(Integer, ForeignKey("tipos_venta.id", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, default=True)

    # Relaciones
    tipo_venta = relationship("TipoVenta", back_populates="categorias")
    productos = relationship("Producto", back_populates="categoria")


class TipoProducto(Base):
    """Tipos de producto: Materia Prima, Producto Elaborado, Insumo, etc."""
    __tablename__ = "tipos_producto"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    productos = relationship("Producto", back_populates="tipo_producto")



class TipoDocumento(Base):
    """Tipos de documento tributario (Factura, Boleta, Guía, etc)."""
    __tablename__ = "tipos_documento_tributario"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    compras = relationship("Compra", back_populates="tipo_documento_rel")
    pedidos = relationship("Pedido", back_populates="tipo_documento_tributario")


class TipoVenta(Base):
    """Tipos de venta: UNITARIO, PESO_SUELTO, CAJA_VARIABLE."""
    __tablename__ = "tipos_venta"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    categorias = relationship("CategoriaProducto", back_populates="tipo_venta")


class TipoProveedor(Base):
    """Tipos de proveedor: CARNES, LACTEOS, PANADERIA, etc."""
    __tablename__ = "tipos_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    proveedores = relationship("Proveedor", back_populates="tipo_proveedor")


class TipoVehiculo(Base):
    """Tipos de vehículo para enrolamiento: CAMION, FURGON, CAMIONETA."""
    __tablename__ = "tipos_vehiculo"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    enrolamientos = relationship("Enrolamiento", back_populates="tipo_vehiculo")


class EstadoEnrolamiento(Base):
    """Estados del proceso de enrolamiento: PENDIENTE, EN_PROCESO, FINALIZADO."""
    __tablename__ = "estados_enrolamiento"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    enrolamientos = relationship("Enrolamiento", back_populates="estado")


class Ubicacion(Base):
    """Ubicaciones físicas dentro del almacén para trazabilidad de lotes."""
    __tablename__ = "ubicaciones"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)  # P1-A-01, P1-B-02, etc.
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    capacidad_maxima = Column(Integer, default=0)  # Número máximo de cajas
    activo = Column(Boolean, default=True)

    # Relaciones
    lotes = relationship("Lote", back_populates="ubicacion")


class UnidadMedida(Base):
    """Unidades de medida con soporte para conversiones."""
    __tablename__ = "unidades_medida"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    simbolo = Column(String, nullable=False)
    tipo = Column(String)  # CANTIDAD, PESO, VOLUMEN
    factor_conversion = Column(Numeric(10, 4))
    unidad_base_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, default=True)

    # Relaciones
    unidad_base = relationship("UnidadMedida", remote_side=[id])
    productos = relationship("Producto", back_populates="unidad_medida")
    recetas_rendimiento = relationship("Receta", back_populates="unidad_rendimiento", foreign_keys="Receta.unidad_rendimiento_id")
    ingredientes = relationship("IngredienteReceta", back_populates="unidad_medida")


class MedioPago(Base):
    """Medios de pago disponibles en el sistema."""
    __tablename__ = "medios_pago"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    permite_cheque = Column(Boolean, default=False)  # Si permite ingresar datos de cheque
    activo = Column(Boolean, default=True)

    # Relaciones
    pedidos = relationship("Pedido", back_populates="medio_pago")
    operaciones_caja = relationship("OperacionCaja", back_populates="medio_pago")


class EstadoCheque(Base):
    """Estados posibles de los cheques (Pendiente, Cobrado, Rechazado, etc.)."""
    __tablename__ = "estados_cheque"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    es_final = Column(Boolean, default=False)  # Si es un estado final (no cambia más)
    activo = Column(Boolean, default=True)

    # Relaciones
    cheques = relationship("Cheque", back_populates="estado")


class Banco(Base):
    """Bancos para gestión de cheques."""
    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    nombre_corto = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    # Relaciones
    cheques = relationship("Cheque", back_populates="banco_rel")


# --------------------------------------------------
# 2. Catálogos Base
# --------------------------------------------------

class Producto(Base):
    """Catálogo de productos."""
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(Text)
    sku = Column(String, nullable=False, index=True)  # Único por tenant, no global
    imagen_url = Column(String, nullable=True)
    codigo_barra = Column(String(50), nullable=True, index=True)  # Número para generar códigos de barra
    
    # Referencias a tablas maestras
    categoria_id = Column(Integer, ForeignKey("categorias_producto.id", ondelete="RESTRICT"), nullable=False)
    tipo_producto_id = Column(Integer, ForeignKey("tipos_producto.id", ondelete="RESTRICT"), nullable=False)
    unidad_medida_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="RESTRICT"), nullable=False)
    
    # Costos y precios
    precio_compra = Column(Numeric(10, 2), nullable=True)  # Para materias primas
    costo_fabricacion = Column(Numeric(10, 2), nullable=True)  # Calculado automáticamente
    
    # Stock
    stock_minimo = Column(Integer, default=0)
    stock_critico = Column(Integer, default=0)
    
    # Flags de comportamiento
    es_vendible = Column(Boolean, default=True)
    es_vendible_web = Column(Boolean, default=False)
    es_ingrediente = Column(Boolean, default=False)
    tiene_receta = Column(Boolean, default=False)
    
    activo = Column(Boolean, default=True)
    
    # Relaciones
    categoria = relationship("CategoriaProducto", back_populates="productos")
    tipo_producto = relationship("TipoProducto", back_populates="productos")
    unidad_medida = relationship("UnidadMedida", back_populates="productos")
    tenant = relationship("Tenant", back_populates="productos", passive_deletes=True)
    
    inventarios = relationship("Inventario", back_populates="producto", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="producto", cascade="all, delete-orphan")
    items_pedido = relationship("ItemPedido", back_populates="producto")
    stock_cajas = relationship("StockCajasProveedor", back_populates="producto", cascade="all, delete-orphan")
    
    # Relaciones de producción
    recetas = relationship("Receta", back_populates="producto", cascade="all, delete-orphan")
    usado_en_recetas = relationship("IngredienteReceta", back_populates="producto_ingrediente")
    
    # Relaciones de compras
    detalles_compra = relationship("DetalleCompra", back_populates="producto")
    
    # Relaciones de etiquetado
    informacion_nutricional = relationship("InformacionNutricional", back_populates="producto", uselist=False, cascade="all, delete-orphan")
    sellos = relationship("ProductoSello", back_populates="producto", cascade="all, delete-orphan")
    
    # Constraints: SKU único por tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'sku', name='uq_producto_tenant_sku'),
    )


class SelloAdvertencia(Base):
    """Sellos de advertencia para productos (Alto en azúcares, Alto en sodio, etc.)."""
    __tablename__ = "sellos_advertencia"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    color = Column(String, default="#000000")  # Color hexadecimal para el diseño
    icono = Column(String)  # Emoji o código de icono
    orden = Column(Integer, default=0)  # Para ordenar en la UI
    activo = Column(Boolean, default=True)

    # Relaciones
    productos = relationship("ProductoSello", back_populates="sello")


class ProductoSello(Base):
    """Relación many-to-many entre productos y sellos de advertencia."""
    __tablename__ = "producto_sellos"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    sello_id = Column(Integer, ForeignKey("sellos_advertencia.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    producto = relationship("Producto", back_populates="sellos")
    sello = relationship("SelloAdvertencia", back_populates="productos")

    __table_args__ = (
        # Un producto no puede tener el mismo sello dos veces
        UniqueConstraint('producto_id', 'sello_id', name='uk_producto_sello'),
    )


class InformacionNutricional(Base):
    """Información nutricional por cada 100g/100ml de producto."""
    __tablename__ = "informacion_nutricional"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Valores por 100g o 100ml
    porcion_referencia = Column(String, default="100g")  # "100g", "100ml", "1 unidad", etc.
    energia_kcal = Column(Numeric(10, 2))  # Energía en kcal
    proteinas_g = Column(Numeric(10, 2))  # Proteínas en gramos
    carbohidratos_g = Column(Numeric(10, 2))  # Carbohidratos totales en gramos
    azucares_g = Column(Numeric(10, 2))  # Azúcares en gramos
    grasas_totales_g = Column(Numeric(10, 2))  # Grasas totales en gramos
    grasas_saturadas_g = Column(Numeric(10, 2))  # Grasas saturadas en gramos
    grasas_trans_g = Column(Numeric(10, 2))  # Grasas trans en gramos
    fibra_g = Column(Numeric(10, 2))  # Fibra dietética en gramos
    sodio_mg = Column(Numeric(10, 2))  # Sodio en miligramos
    
    # Campos adicionales opcionales
    colesterol_mg = Column(Numeric(10, 2))  # Colesterol en miligramos
    calcio_mg = Column(Numeric(10, 2))  # Calcio en miligramos
    hierro_mg = Column(Numeric(10, 2))  # Hierro en miligramos
    vitamina_a_mcg = Column(Numeric(10, 2))  # Vitamina A en microgramos
    vitamina_c_mg = Column(Numeric(10, 2))  # Vitamina C en miligramos
    
    # Metadata
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    producto = relationship("Producto", back_populates="informacion_nutricional")


class Local(Base):
    """Locales o sucursales."""
    __tablename__ = "locales"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo = Column(String, nullable=False, index=True)  # Único por tenant, no global
    nombre = Column(String, nullable=False, index=True)  # Único por tenant, no global
    direccion = Column(String)
    activo = Column(Boolean, default=True)
    tipo_local_id = Column(Integer, ForeignKey("tipos_local.id", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="locales", passive_deletes=True)
    tipo_local = relationship("TipoLocal", back_populates="locales")
    inventarios = relationship("Inventario", back_populates="local", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="local", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="local", foreign_keys="Pedido.local_id")
    compras = relationship("Compra", back_populates="local")
    turnos_caja = relationship("TurnoCaja", back_populates="local", cascade="all, delete-orphan")
    
    # Constraints: codigo y nombre únicos por tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'codigo', name='uq_local_tenant_codigo'),
        UniqueConstraint('tenant_id', 'nombre', name='uq_local_tenant_nombre'),
    )

# --------------------------------------------------
# 11. SOLICITUDES DE TRANSFERENCIA ENTRE LOCALES
# --------------------------------------------------

class SolicitudTransferencia(Base):
    """Solicitud de productos entre locales."""
    __tablename__ = "solicitudes_transferencia"

    solicitud_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    local_origen_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    local_destino_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    usuario_solicitante_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    usuario_finalizador_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    estado_id = Column(Integer, ForeignKey("estados_enrolamiento.id", ondelete="RESTRICT"), nullable=False)
    nota = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    items = relationship("ItemSolicitudTransferencia", back_populates="solicitud", cascade="all, delete-orphan")
    local_origen = relationship("Local", foreign_keys=[local_origen_id])
    local_destino = relationship("Local", foreign_keys=[local_destino_id])
    usuario_solicitante = relationship("User", foreign_keys=[usuario_solicitante_id])
    usuario_finalizador = relationship("User", foreign_keys=[usuario_finalizador_id])
    estado = relationship("EstadoEnrolamiento")
    tenant = relationship("Tenant")


class ItemSolicitudTransferencia(Base):
    """Detalle de productos solicitados en una solicitud de transferencia."""
    __tablename__ = "items_solicitud_transferencia"

    solicitud_item_id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_transferencia.solicitud_id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad_solicitada = Column(Integer, nullable=False)
    cantidad_aprobada = Column(Integer, nullable=True)
    movimiento_inventario_id = Column(Integer, ForeignKey("movimientos_inventario.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    solicitud = relationship("SolicitudTransferencia", back_populates="items")
    producto = relationship("Producto")
    movimiento_inventario = relationship("MovimientoInventario")

class Cliente(Base):
    """Clientes del sistema."""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String)
    email = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_cliente_tenant_email'),
    )
    telefono = Column(String)
    direccion = Column(String)
    comuna = Column(String)
    
    # Campos tributarios
    rut = Column(String, nullable=True, index=True)  # RUT para facturas
    razon_social = Column(String, nullable=True)  # Nombre empresarial
    giro = Column(String, nullable=True)  # Actividad comercial
    es_empresa = Column(Boolean, default=False)  # Si requiere factura
    
    # Campos de crédito
    limite_credito = Column(Numeric(10, 2), nullable=False, default=0.00)
    credito_usado = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Relaciones
    tenant = relationship("Tenant", back_populates="clientes")
    pedidos = relationship("Pedido", back_populates="cliente")
    puntos_cliente = relationship("PuntosCliente", back_populates="cliente", cascade="all, delete-orphan")
    movimientos_puntos = relationship("MovimientoPuntos", back_populates="cliente", cascade="all, delete-orphan")


class TipoMovimientoPuntos(enum.Enum):
    """Tipos de movimientos de puntos."""
    GANADOS = "GANADOS"      # Puntos ganados por compras
    USADOS = "USADOS"        # Puntos usados en compras
    VENCIDOS = "VENCIDOS"    # Puntos vencidos por tiempo
    AJUSTE = "AJUSTE"        # Ajustes manuales


class EstadoSII(enum.Enum):
    """Estados de procesamiento SII para facturas."""
    PENDIENTE = "PENDIENTE"        # Factura creada, pendiente de envío al SII
    ENVIADO = "ENVIADO"           # Enviado al SII, esperando respuesta
    APROBADO = "APROBADO"         # Aprobado por el SII (factura válida)
    RECHAZADO = "RECHAZADO"       # Rechazado por el SII
    ERROR_ENVIO = "ERROR_ENVIO"   # Error técnico al enviar
    NO_APLICA = "NO_APLICA"       # No requiere SII (boletas)


class PuntosCliente(Base):
    """Saldo actual de puntos por cliente."""
    __tablename__ = "puntos_cliente"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    puntos_disponibles = Column(Integer, default=0, nullable=False)
    puntos_totales_ganados = Column(Integer, default=0, nullable=False)
    puntos_totales_usados = Column(Integer, default=0, nullable=False)
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="puntos_cliente")
    
    # Índices
    __table_args__ = (
        UniqueConstraint('cliente_id', name='uq_puntos_cliente_id'),
        Index('ix_puntos_cliente_disponibles', 'puntos_disponibles'),
    )


class MovimientoPuntos(Base):
    """Historial de movimientos de puntos por cliente."""
    __tablename__ = "movimientos_puntos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="SET NULL"), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias_producto.id", ondelete="SET NULL"), nullable=True)
    
    tipo_movimiento = Column(Enum(TipoMovimientoPuntos), nullable=False)
    puntos = Column(Integer, nullable=False)  # Positivo para ganados, negativo para usados
    descripcion = Column(String, nullable=True)
    fecha_movimiento = Column(DateTime, default=func.now(), nullable=False)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="movimientos_puntos")
    pedido = relationship("Pedido")
    categoria = relationship("CategoriaProducto")
    
    # Índices
    __table_args__ = (
        Index('ix_movimientos_puntos_cliente_fecha', 'cliente_id', 'fecha_movimiento'),
        Index('ix_movimientos_puntos_tipo', 'tipo_movimiento'),
        Index('ix_movimientos_puntos_pedido', 'pedido_id'),
    )


# --------------------------------------------------
# 2. Tablas de Inventario y Precios
# --------------------------------------------------

class Inventario(Base):
    """Stock de productos por local."""
    __tablename__ = "inventario"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="CASCADE"), nullable=False)
    cantidad_stock = Column(Integer, nullable=False, default=0)
    
    # Relaciones
    producto = relationship("Producto", back_populates="inventarios")
    local = relationship("Local", back_populates="inventarios")
    
    # Constraint: Un producto solo puede tener una entrada por local
    __table_args__ = (
        UniqueConstraint('producto_id', 'local_id', name='uix_inventario_producto_local'),
    )


class MovimientoInventario(Base):
    """Historial de movimientos de inventario entre locales."""
    __tablename__ = "movimientos_inventario"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    local_origen_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=True)  # NULL = entrada inicial
    local_destino_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=True)  # NULL = salida/ajuste
    cantidad = Column(Integer, nullable=False)
    tipo_movimiento = Column(String, nullable=False)  # TRANSFERENCIA, AJUSTE, PEDIDO, ENTRADA_INICIAL
    referencia_id = Column(Integer, nullable=True)  # ID del pedido si es por pedido
    notas = Column(String)
    usuario = Column(String, default="admin")  # Futuro: FK a tabla usuarios
    fecha_movimiento = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relaciones
    producto = relationship("Producto")
    local_origen = relationship("Local", foreign_keys=[local_origen_id])
    local_destino = relationship("Local", foreign_keys=[local_destino_id])


class Precio(Base):
    """Precios de productos por local y unidad de medida."""
    __tablename__ = "precios"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="CASCADE"), nullable=False)
    unidad_medida_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="RESTRICT"), nullable=False)
    monto_precio = Column(Float, nullable=False)
    fecha_vigencia = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    producto = relationship("Producto", back_populates="precios")
    local = relationship("Local", back_populates="precios")
    unidad_medida = relationship("UnidadMedida")
    
    # Constraint: Un producto solo puede tener un precio activo por local y unidad de medida
    __table_args__ = (
        UniqueConstraint('producto_id', 'local_id', 'unidad_medida_id', name='uix_precio_producto_local_unidad'),
    )


class PrecioProveedor(Base):
    """Precios de productos por proveedor (para cajas variables)."""
    __tablename__ = "precios_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    precio_kg = Column(Numeric(10, 2), nullable=False)  # Precio por kilogramo
    fecha_vigencia = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    notas = Column(String, nullable=True)  # Notas sobre el precio (temporal, promocional, etc.)
    
    # Relaciones
    producto = relationship("Producto")
    proveedor = relationship("Proveedor")
    
    # Constraint: Un producto solo puede tener un precio activo por proveedor
    __table_args__ = (
        UniqueConstraint('producto_id', 'proveedor_id', name='uix_precio_producto_proveedor'),
    )


# --------------------------------------------------
# 3. Tablas de Venta (Transaccionales)
# --------------------------------------------------

class EstadoPedido(Base):
    """Estados configurables para pedidos."""
    __tablename__ = "estados_pedido"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)  # 'PENDIENTE', 'CONFIRMADO'
    nombre = Column(String(100), nullable=False)  # 'Pendiente de Pago'
    descripcion = Column(Text, nullable=True)
    color = Column(String(20), nullable=False, default='gray-500')  # 'yellow-500', 'blue-500'
    orden = Column(Integer, nullable=False, default=0)  # Para ordenar en filtros/UI
    es_final = Column(Boolean, default=False)  # True para ENTREGADO, CANCELADO
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="estado_pedido")


class Pedido(Base):
    """Encabezado de pedidos/ventas."""
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_pedido = Column(String(50), unique=True, nullable=False, index=True)  # ME-2026-00001, EO-2026-00042
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    local_despacho_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=True)  # Local de donde se despacha
    medio_pago_id = Column(Integer, ForeignKey("medios_pago.id", ondelete="RESTRICT"), nullable=True)  # Medio de pago utilizado
    tipo_pedido_id = Column(Integer, ForeignKey("tipos_pedido.id", ondelete="RESTRICT"), nullable=False, default=1)  # Tipo de inventario a usar
    tipo_documento_tributario_id = Column(Integer, ForeignKey("tipos_documento_tributario.id", ondelete="RESTRICT"), nullable=True, default=2)  # BOLETA por defecto (ID 2 = BOL)
    usuario_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Usuario que creó el pedido
    fecha_pedido = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    monto_total = Column(Float, default=0.00)
    estado_id = Column(Integer, ForeignKey("estados_pedido.id", ondelete="RESTRICT"), nullable=False, default=1)  # FK a estados_pedido
    es_pagado = Column(Boolean, default=False)
    inventario_descontado = Column(Boolean, default=False)  # Flag para evitar doble descuento
    notas = Column(Text, nullable=True)
    notas_admin = Column(Text, nullable=True)
    
    # Campos de puntos
    puntos_ganados = Column(Integer, default=0)    # Puntos ganados en este pedido
    puntos_usados = Column(Integer, default=0)     # Puntos usados como descuento
    descuento_puntos = Column(Numeric(10, 2), default=0.00)  # Monto descontado por puntos
    
    # Mercado Pago Fields
    mp_preference_id = Column(String, nullable=True)  # ID de la preferencia de pago
    mp_payment_id = Column(String, nullable=True)     # ID único del pago en MP
    mp_status = Column(String, nullable=True)         # Estado del pago (approved, pending, etc)
    mp_external_reference = Column(String, nullable=True) # Referencia externa (nuestro ID de pedido)
    
    # Control SII (Facturación Electrónica)
    estado_sii = Column(String, nullable=True, default="PENDIENTE")  # PENDIENTE, ENVIADO, APROBADO, RECHAZADO
    folio_sii = Column(String, nullable=True, index=True)  # Número oficial del SII
    numero_dte = Column(String, nullable=True, index=True)  # Número DTE (Documento Tributario Electrónico)
    fecha_envio_sii = Column(DateTime(timezone=True), nullable=True)  # Cuándo se envió al SII
    fecha_respuesta_sii = Column(DateTime(timezone=True), nullable=True)  # Respuesta del SII
    xml_sii = Column(Text, nullable=True)  # XML generado para el SII
    respuesta_sii = Column(Text, nullable=True)  # Respuesta completa del SII
    observaciones_sii = Column(Text, nullable=True)  # Notas sobre el proceso SII

    # Relaciones
    tenant = relationship("Tenant", back_populates="pedidos")
    cliente = relationship("Cliente", back_populates="pedidos")
    usuario = relationship("User", foreign_keys=[usuario_id])
    estado_pedido = relationship("EstadoPedido", back_populates="pedidos")
    local = relationship("Local", back_populates="pedidos", foreign_keys=[local_id])
    local_despacho = relationship("Local", foreign_keys=[local_despacho_id])
    medio_pago = relationship("MedioPago", back_populates="pedidos")
    tipo_pedido = relationship("TipoPedido", back_populates="pedidos")
    tipo_documento_tributario = relationship("TipoDocumento", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    cheques = relationship("Cheque", back_populates="pedido", cascade="all, delete-orphan")
    operacion_caja = relationship("OperacionCaja", back_populates="pedido", uselist=False)
    despacho = relationship("Despacho", back_populates="pedido", uselist=False)


class Cheque(Base):
    """Cheques asociados a pedidos para gestión de cobros."""
    __tablename__ = "cheques"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    estado_id = Column(Integer, ForeignKey("estados_cheque.id", ondelete="RESTRICT"), nullable=False)
    banco_id = Column(Integer, ForeignKey("bancos.id", ondelete="RESTRICT"), nullable=False)
    
    # Datos del cheque
    numero_cheque = Column(String, nullable=False, index=True)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha_emision = Column(DateTime(timezone=True), nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    
    # Datos del librador
    librador_nombre = Column(String, nullable=False)
    librador_rut = Column(String, nullable=True)
    
    # Fechas de gestión
    fecha_recepcion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    fecha_deposito = Column(DateTime(timezone=True), nullable=True)
    fecha_cobro = Column(DateTime(timezone=True), nullable=True)
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="cheques")
    estado = relationship("EstadoCheque", back_populates="cheques")
    banco_rel = relationship("Banco", back_populates="cheques")

class ItemPedido(Base):
    """Detalle de items en cada pedido."""
    __tablename__ = "items_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    lote_id = Column(Integer, ForeignKey("lotes.id", ondelete="RESTRICT"), nullable=True)  # Para productos con trazabilidad
    cantidad = Column(Float, nullable=False)  # Cambiado a Float para permitir decimales (ej: 0.5 kg)
    precio_unitario_venta = Column(Float, nullable=False)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items_pedido")
    lote = relationship("Lote", back_populates="items_pedido")
    
    # Constraint: Un producto no puede repetirse en el mismo pedido (excepto si tiene lotes diferentes)
    __table_args__ = (
        UniqueConstraint('pedido_id', 'producto_id', 'lote_id', name='uix_item_pedido_producto_lote'),
    )


# --------------------------------------------------
# 4. Autenticación y Usuarios
# --------------------------------------------------

class Role(Base):
    """Roles de usuario (e.g., admin, vendedor)."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False, index=True)
    descripcion = Column(String)

    # Relaciones
    users = relationship("User", back_populates="role")
    menus = relationship("MenuItem", secondary="role_menu_permissions", back_populates="roles")


# Tabla Intermedia para RBAC de Menús
role_menu_permissions = Table(
    "role_menu_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_item_id", Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True),
)


class MenuItem(Base):
    """Items del menú lateral configurables por rol."""
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    href = Column(String, nullable=False)
    icon = Column(String)  # Emoji o identificador de icono
    orden = Column(Integer, default=0)
    
    # Relaciones
    roles = relationship("Role", secondary=role_menu_permissions, back_populates="menus")


class User(Base):
    """Usuarios del sistema."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre_completo = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    local_defecto_id = Column(Integer, ForeignKey("locales.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    tenant = relationship("Tenant", back_populates="usuarios")
    role = relationship("Role", back_populates="users")
    local_defecto = relationship("Local", foreign_keys=[local_defecto_id])
    turnos_caja = relationship("TurnoCaja", back_populates="vendedor", cascade="all, delete-orphan")


# --------------------------------------------------
# 5. Sistema de Producción y Recetas
# --------------------------------------------------

class Receta(Base):
    """Recetas de producción para productos elaborados."""
    __tablename__ = "recetas"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    version = Column(Integer, default=1)
    
    # Rendimiento
    rendimiento = Column(Numeric(10, 3), nullable=False)
    unidad_rendimiento_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="RESTRICT"), nullable=False)
    
    # Costos calculados automáticamente
    costo_total_calculado = Column(Numeric(10, 2))
    costo_unitario_calculado = Column(Numeric(10, 2))
    
    # Metadata
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    activa = Column(Boolean, default=True)
    notas = Column(Text)
    
    # Relaciones
    producto = relationship("Producto", back_populates="recetas")
    unidad_rendimiento = relationship("UnidadMedida", back_populates="recetas_rendimiento", foreign_keys=[unidad_rendimiento_id])
    ingredientes = relationship("IngredienteReceta", back_populates="receta", cascade="all, delete-orphan")


class IngredienteReceta(Base):
    """Ingredientes que componen una receta."""
    __tablename__ = "ingredientes_receta"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("recetas.id", ondelete="CASCADE"), nullable=False)
    producto_ingrediente_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    
    # Cantidad del ingrediente
    cantidad = Column(Numeric(10, 3), nullable=False)
    unidad_medida_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="RESTRICT"), nullable=False)
    
    # Costos
    costo_unitario_referencia = Column(Numeric(10, 2))
    costo_total_calculado = Column(Numeric(10, 2))
    
    orden = Column(Integer, default=0)
    notas = Column(String)
    
    # Relaciones
    receta = relationship("Receta", back_populates="ingredientes")
    producto_ingrediente = relationship("Producto", back_populates="usado_en_recetas")
    unidad_medida = relationship("UnidadMedida", back_populates="ingredientes")


# --------------------------------------------------
# 6. Ordenes de Producción
# --------------------------------------------------

class OrdenProduccion(Base):
    """Orden de producción de productos elaborados."""
    __tablename__ = "ordenes_produccion"

    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    fecha_programada = Column(DateTime(timezone=True), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_finalizacion = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String, default="PLANIFICADA") # PLANIFICADA, FINALIZADA, CANCELADA
    notas = Column(Text)
    
    # Relaciones
    local = relationship("Local")
    detalles = relationship("DetalleOrdenProduccion", back_populates="orden", cascade="all, delete-orphan")


class DetalleOrdenProduccion(Base):
    """Detalle de productos a producir."""
    __tablename__ = "detalles_orden_produccion"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_produccion.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    unidad_medida_id = Column(Integer, ForeignKey("unidades_medida.id", ondelete="RESTRICT"), nullable=False)
    
    cantidad_programada = Column(Numeric(10, 3), nullable=False)
    cantidad_producida = Column(Numeric(10, 3), nullable=True) # Se llena al finalizar
    
    # Relaciones
    orden = relationship("OrdenProduccion", back_populates="detalles")
    producto = relationship("Producto")
    unidad_medida = relationship("UnidadMedida")

    @property
    def producto_nombre(self):
        return self.producto.nombre if self.producto else None

# --------------------------------------------------
# 7. Compras y Proveedores (Nuevo)
# --------------------------------------------------

class Proveedor(Base):
    """Proveedores para compras de insumos."""
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    rut = Column(String, unique=True, index=True)
    contacto = Column(String)
    email = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    tipo_proveedor_id = Column(Integer, ForeignKey("tipos_proveedor.id", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, default=True)

    # Relaciones
    tenant = relationship("Tenant", back_populates="proveedores")
    tipo_proveedor = relationship("TipoProveedor", back_populates="proveedores")
    compras = relationship("Compra", back_populates="proveedor")
    enrolamientos = relationship("Enrolamiento", back_populates="proveedor")
    stock_cajas = relationship("StockCajasProveedor", back_populates="proveedor", cascade="all, delete-orphan")


class Enrolamiento(Base):
    """Sistema de enrolamiento de vehículos para recepción de mercadería."""
    __tablename__ = "enrolamientos"

    id = Column(Integer, primary_key=True, index=True)
    
    # Datos del vehículo
    tipo_vehiculo_id = Column(Integer, ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"), nullable=False)
    patente = Column(String, nullable=False, index=True)
    chofer = Column(String, nullable=False)
    
    # Datos del proveedor y documento
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="RESTRICT"), nullable=False)
    numero_documento = Column(String, nullable=False)  # Número de guía o factura
    
    # Control de proceso
    estado_id = Column(Integer, ForeignKey("estados_enrolamiento.id", ondelete="RESTRICT"), nullable=False)
    usuario_registro_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_termino = Column(DateTime(timezone=True), nullable=True)
    
    # Observaciones
    notas = Column(Text)
    
    # Relaciones
    tipo_vehiculo = relationship("TipoVehiculo", back_populates="enrolamientos")
    proveedor = relationship("Proveedor", back_populates="enrolamientos")
    estado = relationship("EstadoEnrolamiento", back_populates="enrolamientos")
    usuario_registro = relationship("User", foreign_keys=[usuario_registro_id])
    lotes = relationship("Lote", back_populates="enrolamiento")


class Lote(Base):
    """Lotes individuales para trazabilidad de productos con caja variable (especialmente carnes)."""
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_lote = Column(String, unique=True, nullable=False, index=True)  # Código generado único
    
    # Relación con enrolamiento (cuando está finalizado)
    enrolamiento_id = Column(Integer, ForeignKey("enrolamientos.id", ondelete="RESTRICT"), nullable=False)
    
    # Datos del producto y ubicación
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    ubicacion_id = Column(Integer, ForeignKey("ubicaciones.id", ondelete="RESTRICT"), nullable=False)
    
    # Información de trazabilidad
    qr_original = Column(String, nullable=True)  # QR extraído de la etiqueta original
    lote_proveedor = Column(String, nullable=True)  # Número de lote del proveedor
    qr_propio = Column(String, unique=True, nullable=False, index=True)  # QR generado por nosotros
    
    # Pesos y fechas
    peso_original = Column(Numeric(8, 3), nullable=False)  # Peso extraído de la etiqueta
    peso_actual = Column(Numeric(8, 3), nullable=False)    # Peso actual (puede cambiar)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    fecha_fabricacion = Column(DateTime(timezone=True), nullable=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Estado del lote
    disponible_venta = Column(Boolean, default=False)  # Solo True cuando enrolamiento está FINALIZADO
    vendido = Column(Boolean, default=False)
    
    # Archivos e imágenes
    foto_etiqueta = Column(String, nullable=True)  # Ruta de la foto de la etiqueta original
    
    # Relaciones
    enrolamiento = relationship("Enrolamiento", back_populates="lotes")
    producto = relationship("Producto", foreign_keys=[producto_id])
    ubicacion = relationship("Ubicacion", back_populates="lotes")
    items_pedido = relationship("ItemPedido", back_populates="lote")


class Compra(Base):
    """Cabecera de compras de mercadería."""
    __tablename__ = "compras"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="RESTRICT"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    
    # Cambiado de String a FK
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento_tributario.id", ondelete="RESTRICT"), nullable=False)
    
    fecha_compra = Column(DateTime(timezone=True), server_default=func.now())
    numero_documento = Column(String)  # Fac/Bol/Guia
    monto_total = Column(Numeric(10, 2), default=0)
    notas = Column(Text)
    estado = Column(String, default="RECIBIDA") # RECIBIDA, ANULADA
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="compras")
    local = relationship("Local", back_populates="compras")
    tipo_documento_rel = relationship("TipoDocumento", back_populates="compras")
    detalles = relationship("DetalleCompra", back_populates="compra", cascade="all, delete-orphan")


class DetalleCompra(Base):
    """Detalle de productos comprados."""
    __tablename__ = "detalles_compra"

    id = Column(Integer, primary_key=True, index=True)
    compra_id = Column(Integer, ForeignKey("compras.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Numeric(10, 3), nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False) # Precio Costo Unitario
    
    # Relaciones
    compra = relationship("Compra", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_compra")


# --------------------------------------------------
# 8. Sistema de Caja (Flujo de Caja para Vendedores)
# --------------------------------------------------

class EstadoTurnoCaja(enum.Enum):
    """Estados posibles de un turno de caja."""
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"


class TipoOperacionCaja(enum.Enum):
    """Tipos de operaciones de caja."""
    APERTURA = "APERTURA"          # Monto inicial al abrir caja
    VENTA = "VENTA"                # Venta realizada (automática desde pedidos)
    INGRESO = "INGRESO"            # Ingreso manual (pagos, otros)
    EGRESO = "EGRESO"              # Egreso manual (gastos, cambio)
    DEVOLUCION = "DEVOLUCION"      # Devolución de dinero
    CIERRE = "CIERRE"              # Registro del cierre de caja


class TurnoCaja(Base):
    """Turnos de caja por vendedor - Control de apertura y cierre."""
    __tablename__ = "turnos_caja"

    id = Column(Integer, primary_key=True, index=True)
    vendedor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    
    # Control de turno
    fecha_apertura = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True, index=True)
    estado = Column(Enum(EstadoTurnoCaja), nullable=False, default=EstadoTurnoCaja.ABIERTO, index=True)
    
    # Montos de control
    monto_inicial = Column(Numeric(10, 2), nullable=False, default=0.00)  # Efectivo al abrir
    efectivo_esperado = Column(Numeric(10, 2), nullable=True)  # Calculado automáticamente
    efectivo_real = Column(Numeric(10, 2), nullable=True)  # Contado físicamente al cerrar
    diferencia = Column(Numeric(10, 2), nullable=True)  # efectivo_real - efectivo_esperado
    
    # Observaciones
    observaciones_apertura = Column(Text, nullable=True)
    observaciones_cierre = Column(Text, nullable=True)
    
    # Relaciones
    vendedor = relationship("User", back_populates="turnos_caja")
    local = relationship("Local", back_populates="turnos_caja")
    operaciones = relationship("OperacionCaja", back_populates="turno", cascade="all, delete-orphan")

    # Restricción: Solo un turno abierto por vendedor-local
    __table_args__ = (
        Index("idx_turno_vendedor_abierto", "vendedor_id", "local_id", "estado"),
    )


class OperacionCaja(Base):
    """Registro de operaciones individuales en caja."""
    __tablename__ = "operaciones_caja"

    id = Column(Integer, primary_key=True, index=True)
    turno_caja_id = Column(Integer, ForeignKey("turnos_caja.id", ondelete="CASCADE"), nullable=False)
    
    # Datos de la operación
    tipo_operacion = Column(Enum(TipoOperacionCaja), nullable=False, index=True)
    fecha_operacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    monto = Column(Numeric(10, 2), nullable=False)
    descripcion = Column(String, nullable=False)
    observaciones = Column(Text, nullable=True)
    
    # Referencias opcionales
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="SET NULL"), nullable=True)  # Si viene de una venta
    medio_pago_id = Column(Integer, ForeignKey("medios_pago.id", ondelete="RESTRICT"), nullable=True)  # Efectivo, tarjeta, etc.
    
    # Relaciones
    turno = relationship("TurnoCaja", back_populates="operaciones")
    pedido = relationship("Pedido", back_populates="operacion_caja")
    medio_pago = relationship("MedioPago", back_populates="operaciones_caja")


# --------------------------------------------------
# 10. STOCK CAJAS PROVEEDOR
# --------------------------------------------------

class StockCajasProveedor(Base):
    """Stock de cajas por proveedor para productos de peso variable."""
    __tablename__ = "stock_cajas_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    
    # Stock
    cajas_disponibles = Column(Integer, nullable=False, default=0)
    cajas_totales_recibidas = Column(Integer, nullable=False, default=0)
    cajas_totales_vendidas = Column(Integer, nullable=False, default=0)
    
    # Métricas
    peso_promedio_caja_kg = Column(Float, nullable=True)  # Peso promedio por caja
    
    # Control temporal
    fecha_ultima_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    # Relaciones
    producto = relationship("Producto", back_populates="stock_cajas")
    proveedor = relationship("Proveedor", back_populates="stock_cajas")
    movimientos = relationship("MovimientoStockCajas", back_populates="stock_cajas", cascade="all, delete-orphan")
    
    # Restricción única por producto-proveedor
    __table_args__ = (
        UniqueConstraint('producto_id', 'proveedor_id', name='uix_stock_cajas_producto_proveedor'),
    )


class MovimientoStockCajas(Base):
    """Historial de movimientos de stock de cajas por proveedor."""
    __tablename__ = "movimientos_stock_cajas"

    id = Column(Integer, primary_key=True, index=True)
    
    # Referencias principales
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="RESTRICT"), nullable=False)
    stock_cajas_id = Column(Integer, ForeignKey("stock_cajas_proveedor.id", ondelete="CASCADE"), nullable=True)
    
    # Referencias opcionales
    lote_id = Column(Integer, ForeignKey("lotes.id", ondelete="SET NULL"), nullable=True)
    enrolamiento_id = Column(Integer, ForeignKey("enrolamientos.id", ondelete="SET NULL"), nullable=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="SET NULL"), nullable=True)
    
    # Datos del movimiento
    tipo_movimiento = Column(String, nullable=False, index=True)  # ENTRADA_ENROLAMIENTO, VENTA_LOTE, DEVOLUCION_LOTE, etc.
    cajas_movimiento = Column(Integer, nullable=False)  # Cantidad de cajas (positivo=entrada, negativo=salida)
    peso_total_kg = Column(Float, nullable=True)  # Peso total movido
    
    # Estado antes y después
    cajas_antes = Column(Integer, nullable=False, default=0)
    cajas_despues = Column(Integer, nullable=False, default=0)
    
    # Metadatos
    descripcion = Column(String, nullable=True)
    usuario = Column(String, nullable=True)
    fecha_movimiento = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Referencias adicionales para trazabilidad
    lote_codigo = Column(String, nullable=True, index=True)  # Código del lote específico
    referencia_tipo = Column(String, nullable=True)  # PEDIDO, AJUSTE, etc.
    referencia_id = Column(Integer, nullable=True)  # ID de la referencia
    notas = Column(Text, nullable=True)
    
    # Relaciones
    producto = relationship("Producto")
    proveedor = relationship("Proveedor")
    stock_cajas = relationship("StockCajasProveedor", back_populates="movimientos")
    lote = relationship("Lote")
    enrolamiento = relationship("Enrolamiento")
    pedido = relationship("Pedido")
    
    # Índices para performance
    __table_args__ = (
        Index('ix_movimientos_stock_cajas_fecha', 'fecha_movimiento'),
        Index('ix_movimientos_stock_cajas_tipo', 'tipo_movimiento'),
        Index('ix_movimientos_stock_cajas_producto_proveedor', 'producto_id', 'proveedor_id'),
        Index('ix_movimientos_stock_cajas_lote_codigo', 'lote_codigo'),
    )


# --------------------------------------------------
# 10. SISTEMA DE DESPACHOS
# --------------------------------------------------

class EstadoDespacho(enum.Enum):
    """Estados del proceso de despacho."""
    ASIGNADO = "ASIGNADO"
    EN_PICKING = "EN_PICKING"
    LISTO_EMPAQUE = "LISTO_EMPAQUE"
    EN_RUTA = "EN_RUTA"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class Despacho(Base):
    """Gestión de despachos de pedidos."""
    __tablename__ = "despachos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, unique=True)
    despachador_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estado_despacho = Column(Enum(EstadoDespacho), default=EstadoDespacho.ASIGNADO, nullable=False)
    
    # Timestamps del proceso
    fecha_asignacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_inicio_picking = Column(DateTime(timezone=True), nullable=True)
    fecha_fin_picking = Column(DateTime(timezone=True), nullable=True)
    fecha_inicio_ruta = Column(DateTime(timezone=True), nullable=True)
    fecha_entrega = Column(DateTime(timezone=True), nullable=True)
    
    # Información adicional
    notas_despacho = Column(Text, nullable=True)
    ubicacion_actual = Column(String, nullable=True)  # GPS coords "lat,lng"
    hora_estimada_entrega = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="despacho")
    despachador = relationship("User")
    picking_items = relationship("PickingItem", back_populates="despacho", cascade="all, delete-orphan")


class PickingItem(Base):
    """Items individuales del proceso de picking."""
    __tablename__ = "picking_items"

    id = Column(Integer, primary_key=True, index=True)
    despacho_id = Column(Integer, ForeignKey("despachos.id", ondelete="CASCADE"), nullable=False)
    item_pedido_id = Column(Integer, ForeignKey("items_pedido.id", ondelete="CASCADE"), nullable=False)
    usuario_picking_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Cantidades para productos regulares
    cantidad_solicitada = Column(Integer, nullable=True)
    cantidad_pickeada = Column(Integer, nullable=True)
    
    # Datos específicos para cajas variables
    lote_codigo = Column(String, nullable=True)  # Para cajas variables
    peso_solicitado = Column(Numeric(10, 3), nullable=True)  # kg estimado
    peso_real = Column(Numeric(10, 3), nullable=True)  # kg real pickeado
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=True)
    
    # Información de ubicación y proceso
    ubicacion_picking = Column(String, nullable=True)  # "FRIGORIFICO-F1-A2"
    codigo_barras_escaneado = Column(String, nullable=True)
    fecha_picking = Column(DateTime(timezone=True), nullable=True)
    notas_picking = Column(Text, nullable=True)
    completado = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    despacho = relationship("Despacho", back_populates="picking_items")
    item_pedido = relationship("ItemPedido")
    usuario_picking = relationship("User")

    # Índices
    __table_args__ = (
        Index('ix_picking_items_despacho', 'despacho_id'),
        Index('ix_picking_items_item_pedido', 'item_pedido_id'),
        Index('ix_picking_items_lote', 'lote_codigo'),
    )
