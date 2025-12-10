"""
Modelos de la base de datos con SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# --------------------------------------------------
# 1. Catálogos Base
# --------------------------------------------------

class Producto(Base):
    """Catálogo de productos."""
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(String)
    sku = Column(String, unique=True, nullable=False)
    imagen_url = Column(String, nullable=True)  # URL o path de la imagen del producto
    
    # Relaciones
    inventarios = relationship("Inventario", back_populates="producto", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="producto", cascade="all, delete-orphan")
    items_pedido = relationship("ItemPedido", back_populates="producto")


class Local(Base):
    """Locales o sucursales."""
    __tablename__ = "locales"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)
    nombre = Column(String, unique=True, nullable=False, index=True)
    direccion = Column(String)
    
    # Relaciones
    # Relaciones
    inventarios = relationship("Inventario", back_populates="local", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="local", cascade="all, delete-orphan")
    pedidos = relationship("Pedido", back_populates="local", foreign_keys="Pedido.local_id")


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
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="cliente")


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
    fecha_pedido = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    monto_total = Column(Float, default=0.00)
    estado = Column(String, nullable=False, default="PENDIENTE")  # PENDIENTE, CONFIRMADO, EN_PREPARACION, ENTREGADO, CANCELADO
    es_pagado = Column(Boolean, default=False)
    inventario_descontado = Column(Boolean, default=False)  # Flag para evitar doble descuento
    notas = Column(Text, nullable=True)
    notas_admin = Column(Text, nullable=True)
    
    # Mercado Pago Fields
    mp_preference_id = Column(String, nullable=True)  # ID de la preferencia de pago
    mp_payment_id = Column(String, nullable=True)     # ID único del pago en MP
    mp_status = Column(String, nullable=True)         # Estado del pago (approved, pending, etc)
    mp_external_reference = Column(String, nullable=True) # Referencia externa (nuestro ID de pedido)

    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    local = relationship("Local", back_populates="pedidos", foreign_keys=[local_id])
    local_despacho = relationship("Local", foreign_keys=[local_despacho_id])
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


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
