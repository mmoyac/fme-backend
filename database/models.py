"""
Modelos de la base de datos con SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, Text, Table, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


# --------------------------------------------------
# 1. TABLAS MAESTRAS
# --------------------------------------------------

class CategoriaProducto(Base):
    """Categorías de productos para clasificación y puntos de fidelidad."""
    __tablename__ = "categorias_producto"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String)
    puntos_fidelidad = Column(Integer, default=0)
    activo = Column(Boolean, default=True)

    # Relaciones
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
    activo = Column(Boolean, default=True)

    # Relaciones
    compras = relationship("Compra", back_populates="tipo_documento_rel")


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
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(Text)
    sku = Column(String, unique=True, nullable=False, index=True)
    imagen_url = Column(String, nullable=True)
    
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
    
    inventarios = relationship("Inventario", back_populates="producto", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="producto", cascade="all, delete-orphan")
    items_pedido = relationship("ItemPedido", back_populates="producto")
    
    # Relaciones de producción
    recetas = relationship("Receta", back_populates="producto", cascade="all, delete-orphan")
    usado_en_recetas = relationship("IngredienteReceta", back_populates="producto_ingrediente")
    
    # Relaciones de compras
    detalles_compra = relationship("DetalleCompra", back_populates="producto")


class Local(Base):
    """Locales o sucursales."""
    __tablename__ = "locales"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, unique=True, nullable=False, index=True)
    direccion = Column(String)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    inventarios = relationship("Inventario", back_populates="local", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="local", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="local", foreign_keys="Pedido.local_id")
    compras = relationship("Compra", back_populates="local")


class Cliente(Base):
    """Clientes del sistema."""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String)
    email = Column(String, unique=True)
    telefono = Column(String)
    direccion = Column(String)
    comuna = Column(String)
    
    # Campos de crédito
    limite_credito = Column(Numeric(10, 2), nullable=False, default=0.00)
    credito_usado = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="cliente")
    puntos_cliente = relationship("PuntosCliente", back_populates="cliente")
    movimientos_puntos = relationship("MovimientoPuntos", back_populates="cliente")


class TipoMovimientoPuntos(enum.Enum):
    """Tipos de movimientos de puntos."""
    GANADOS = "GANADOS"      # Puntos ganados por compras
    USADOS = "USADOS"        # Puntos usados en compras
    VENCIDOS = "VENCIDOS"    # Puntos vencidos por tiempo
    AJUSTE = "AJUSTE"        # Ajustes manuales


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
    """Precios de productos por local."""
    __tablename__ = "precios"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="CASCADE"), nullable=False)
    monto_precio = Column(Float, nullable=False)
    fecha_vigencia = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    producto = relationship("Producto", back_populates="precios")
    local = relationship("Local", back_populates="precios")
    
    # Constraint: Un producto solo puede tener un precio activo por local
    __table_args__ = (
        UniqueConstraint('producto_id', 'local_id', name='uix_precio_producto_local'),
    )


# --------------------------------------------------
# 3. Tablas de Venta (Transaccionales)
# --------------------------------------------------

class Pedido(Base):
    """Encabezado de pedidos/ventas."""
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=False)
    local_despacho_id = Column(Integer, ForeignKey("locales.id", ondelete="RESTRICT"), nullable=True)  # Local de donde se despacha
    medio_pago_id = Column(Integer, ForeignKey("medios_pago.id", ondelete="RESTRICT"), nullable=True)  # Medio de pago utilizado
    fecha_pedido = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    monto_total = Column(Float, default=0.00)
    estado = Column(String, nullable=False, default="PENDIENTE")  # PENDIENTE, CONFIRMADO, EN_PREPARACION, ENTREGADO, CANCELADO
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

    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    local = relationship("Local", back_populates="pedidos", foreign_keys=[local_id])
    local_despacho = relationship("Local", foreign_keys=[local_despacho_id])
    medio_pago = relationship("MedioPago", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    cheques = relationship("Cheque", back_populates="pedido", cascade="all, delete-orphan")


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
    cantidad = Column(Integer, nullable=False)
    precio_unitario_venta = Column(Float, nullable=False)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items_pedido")
    
    # Constraint: Un producto no puede repetirse en el mismo pedido
    __table_args__ = (
        UniqueConstraint('pedido_id', 'producto_id', name='uix_item_pedido_producto'),
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
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    nombre_completo = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    role = relationship("Role", back_populates="users")


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
    nombre = Column(String, nullable=False, index=True)
    rut = Column(String, unique=True, index=True)
    contacto = Column(String)
    email = Column(String)
    telefono = Column(String)
    direccion = Column(String)
    activo = Column(Boolean, default=True)

    # Relaciones
    compras = relationship("Compra", back_populates="proveedor")


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
