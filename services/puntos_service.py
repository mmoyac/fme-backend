"""
Servicio para gestionar puntos de clientes.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from database.models import (
    Cliente,
    PuntosCliente,
    MovimientoPuntos,
    TipoMovimientoPuntos,
    Pedido,
    ItemPedido,
    Producto
)


class PuntosService:
    """Servicio para manejar sistema de puntos de clientes."""

    @staticmethod
    def obtener_puntos_cliente(db: Session, cliente_id: int) -> PuntosCliente:
        """
        Obtiene o crea el registro de puntos para un cliente.
        
        Args:
            db: Sesión de base de datos
            cliente_id: ID del cliente
            
        Returns:
            PuntosCliente: Registro de puntos del cliente
        """
        puntos_cliente = db.query(PuntosCliente).filter(
            PuntosCliente.cliente_id == cliente_id
        ).first()
        
        if not puntos_cliente:
            # Crear registro inicial
            puntos_cliente = PuntosCliente(
                cliente_id=cliente_id,
                puntos_disponibles=0,
                puntos_totales_ganados=0,
                puntos_totales_usados=0
            )
            db.add(puntos_cliente)
            db.commit()
            db.refresh(puntos_cliente)
        
        return puntos_cliente

    @staticmethod
    def calcular_puntos_por_pedido(db: Session, pedido_id: int) -> int:
        """
        Calcula los puntos a ganar por un pedido basado en las categorías de productos.
        
        Args:
            db: Sesión de base de datos
            pedido_id: ID del pedido
            
        Returns:
            int: Total de puntos a ganar
        """
        total_puntos = 0
        
        # Obtener items del pedido con productos y categorías
        items = (
            db.query(ItemPedido)
            .join(Producto, ItemPedido.producto_id == Producto.id)
            .filter(ItemPedido.pedido_id == pedido_id)
            .all()
        )
        
        for item in items:
            categoria = item.producto.categoria
            if categoria and categoria.puntos_fidelidad:
                # Puntos por categoría * cantidad comprada
                puntos_item = categoria.puntos_fidelidad * item.cantidad
                total_puntos += puntos_item
        
        return total_puntos

    @staticmethod
    def otorgar_puntos_por_pedido(
        db: Session, 
        cliente_id: int, 
        pedido_id: int,
        puntos: int,
        descripcion: str = None
    ) -> MovimientoPuntos:
        """
        Otorga puntos a un cliente por un pedido confirmado.
        
        Args:
            db: Sesión de base de datos
            cliente_id: ID del cliente
            pedido_id: ID del pedido
            puntos: Cantidad de puntos a otorgar
            descripcion: Descripción opcional del movimiento
            
        Returns:
            MovimientoPuntos: Registro del movimiento creado
        """
        if puntos <= 0:
            return None
        
        # Obtener registro de puntos del cliente
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente_id)
        
        # Crear movimiento de puntos ganados
        movimiento = MovimientoPuntos(
            cliente_id=cliente_id,
            pedido_id=pedido_id,
            tipo_movimiento=TipoMovimientoPuntos.GANADOS,
            puntos=puntos,
            descripcion=descripcion or f"Puntos ganados por pedido #{pedido_id}",
            fecha_movimiento=datetime.now()
        )
        db.add(movimiento)
        
        # Actualizar puntos del cliente
        puntos_cliente.puntos_totales_ganados += puntos
        puntos_cliente.puntos_disponibles += puntos
        
        db.commit()
        db.refresh(movimiento)
        
        return movimiento

    @staticmethod
    def usar_puntos_en_pedido(
        db: Session,
        cliente_id: int,
        pedido_id: int,
        puntos_usar: int,
        descuento_monto: Decimal
    ) -> Tuple[bool, str, Optional[MovimientoPuntos]]:
        """
        Usa puntos de un cliente en un pedido para obtener descuento.
        
        Args:
            db: Sesión de base de datos
            cliente_id: ID del cliente
            pedido_id: ID del pedido
            puntos_usar: Cantidad de puntos a usar
            descuento_monto: Monto del descuento aplicado
            
        Returns:
            Tuple[bool, str, MovimientoPuntos]: 
            - bool: True si la operación fue exitosa
            - str: Mensaje de resultado
            - MovimientoPuntos: Registro del movimiento (si exitoso)
        """
        if puntos_usar <= 0:
            return False, "La cantidad de puntos a usar debe ser mayor a 0", None
        
        # Obtener puntos disponibles del cliente
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente_id)
        
        if puntos_cliente.puntos_disponibles < puntos_usar:
            return False, f"Cliente solo tiene {puntos_cliente.puntos_disponibles} puntos disponibles", None
        
        # Crear movimiento de puntos usados
        movimiento = MovimientoPuntos(
            cliente_id=cliente_id,
            pedido_id=pedido_id,
            tipo_movimiento=TipoMovimientoPuntos.USADOS,
            puntos=puntos_usar,
            descripcion=f"Puntos usados en pedido #{pedido_id} - Descuento: ${descuento_monto:,.0f}",
            fecha_movimiento=datetime.now()
        )
        db.add(movimiento)
        
        # Actualizar puntos del cliente
        puntos_cliente.puntos_totales_usados += puntos_usar
        puntos_cliente.puntos_disponibles -= puntos_usar
        
        db.commit()
        db.refresh(movimiento)
        
        return True, "Puntos usados exitosamente", movimiento

    @staticmethod
    def calcular_descuento_por_puntos(puntos_usar: int, valor_punto: Decimal = Decimal('1')) -> Decimal:
        """
        Calcula el descuento en pesos basado en puntos a usar.
        
        Args:
            puntos_usar: Cantidad de puntos a usar
            valor_punto: Valor en pesos de cada punto (default: $1)
            
        Returns:
            Decimal: Monto del descuento
        """
        return Decimal(puntos_usar) * valor_punto

    @staticmethod
    def obtener_historial_puntos(
        db: Session,
        cliente_id: int,
        limite: int = 50,
        offset: int = 0
    ) -> List[MovimientoPuntos]:
        """
        Obtiene el historial de movimientos de puntos de un cliente.
        
        Args:
            db: Sesión de base de datos
            cliente_id: ID del cliente
            limite: Cantidad máxima de registros
            offset: Número de registros a saltar
            
        Returns:
            List[MovimientoPuntos]: Lista de movimientos de puntos
        """
        return (
            db.query(MovimientoPuntos)
            .filter(MovimientoPuntos.cliente_id == cliente_id)
            .order_by(MovimientoPuntos.fecha_movimiento.desc())
            .limit(limite)
            .offset(offset)
            .all()
        )

    @staticmethod
    def obtener_estadisticas_puntos(db: Session) -> Dict:
        """
        Obtiene estadísticas generales del sistema de puntos.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Dict: Estadísticas del sistema de puntos
        """
        # Total de puntos en el sistema
        total_stats = (
            db.query(
                func.sum(PuntosCliente.puntos_totales_ganados).label('total_ganados'),
                func.sum(PuntosCliente.puntos_totales_usados).label('total_usados'),
                func.sum(PuntosCliente.puntos_disponibles).label('total_disponibles'),
                func.count(PuntosCliente.cliente_id).label('clientes_con_puntos')
            ).first()
        )
        
        # Movimientos por tipo este mes
        fecha_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        movimientos_mes = (
            db.query(
                MovimientoPuntos.tipo_movimiento,
                func.sum(MovimientoPuntos.puntos).label('total_puntos'),
                func.count(MovimientoPuntos.id).label('cantidad_movimientos')
            )
            .filter(MovimientoPuntos.fecha_movimiento >= fecha_inicio_mes)
            .group_by(MovimientoPuntos.tipo_movimiento)
            .all()
        )
        
        # Top 10 clientes con más puntos
        top_clientes = (
            db.query(
                Cliente.nombre,
                Cliente.email,
                PuntosCliente.puntos_disponibles
            )
            .join(PuntosCliente, Cliente.id == PuntosCliente.cliente_id)
            .order_by(PuntosCliente.puntos_disponibles.desc())
            .limit(10)
            .all()
        )
        
        return {
            'total_ganados': int(total_stats.total_ganados or 0),
            'total_usados': int(total_stats.total_usados or 0),
            'total_disponibles': int(total_stats.total_disponibles or 0),
            'clientes_con_puntos': int(total_stats.clientes_con_puntos or 0),
            'movimientos_mes': [
                {
                    'tipo': mov.tipo_movimiento,
                    'total_puntos': int(mov.total_puntos),
                    'cantidad_movimientos': int(mov.cantidad_movimientos)
                }
                for mov in movimientos_mes
            ],
            'top_clientes': [
                {
                    'nombre': cliente.nombre,
                    'email': cliente.email,
                    'puntos_disponibles': int(cliente.puntos_disponibles)
                }
                for cliente in top_clientes
            ]
        }

    @staticmethod
    def validar_uso_puntos_en_total(
        puntos_disponibles: int,
        puntos_usar: int,
        total_pedido: Decimal,
        valor_punto: Decimal = Decimal('1')
    ) -> Tuple[bool, str, Decimal]:
        """
        Valida si se pueden usar los puntos solicitados y calcula el descuento.
        
        Args:
            puntos_disponibles: Puntos disponibles del cliente
            puntos_usar: Puntos que el cliente quiere usar
            total_pedido: Total del pedido antes del descuento
            valor_punto: Valor en pesos de cada punto
            
        Returns:
            Tuple[bool, str, Decimal]:
            - bool: True si es válido
            - str: Mensaje de validación
            - Decimal: Monto del descuento aplicable
        """
        if puntos_usar <= 0:
            return False, "La cantidad de puntos debe ser mayor a 0", Decimal('0')
        
        if puntos_usar > puntos_disponibles:
            return False, f"Solo tienes {puntos_disponibles} puntos disponibles", Decimal('0')
        
        descuento = PuntosService.calcular_descuento_por_puntos(puntos_usar, valor_punto)
        
        if descuento > total_pedido:
            # No se puede descontar más del total del pedido
            puntos_maximos = int(total_pedido / valor_punto)
            descuento_maximo = PuntosService.calcular_descuento_por_puntos(puntos_maximos, valor_punto)
            return False, f"El descuento (${descuento:,.0f}) no puede ser mayor al total del pedido (${total_pedido:,.0f}). Máximo: {puntos_maximos} puntos", descuento_maximo
        
        return True, "Puntos válidos para usar", descuento