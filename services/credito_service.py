"""
Servicio para gestión de crédito de clientes.
"""
from typing import Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from database.models import Cliente, Pedido, EstadoCheque
from schemas.cliente import ClienteResponse


class CreditoService:
    """
    Servicio para manejar operaciones de crédito de clientes.
    """
    
    @staticmethod
    def validar_credito_disponible(
        cliente_id: int, 
        monto_pedido: float, 
        db: Session
    ) -> tuple[bool, str]:
        """
        Valida si el cliente tiene crédito suficiente para un pedido.
        
        Args:
            cliente_id: ID del cliente
            monto_pedido: Monto del pedido que se quiere crear
            db: Sesión de base de datos
            
        Returns:
            tuple: (es_valido, mensaje)
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return False, "Cliente no encontrado"
        
        credito_disponible = float(cliente.limite_credito - cliente.credito_usado)
        
        if monto_pedido > credito_disponible:
            return False, f"Crédito insuficiente. Disponible: ${credito_disponible:,.0f}, Requerido: ${monto_pedido:,.0f}"
        
        return True, "Crédito suficiente"
    
    @staticmethod
    def ocupar_credito(cliente_id: int, monto: float, db: Session) -> bool:
        """
        Ocupa crédito del cliente (cuando se crea un pedido con cheques).
        
        Args:
            cliente_id: ID del cliente
            monto: Monto a ocupar del crédito
            db: Sesión de base de datos
            
        Returns:
            bool: True si se pudo ocupar el crédito
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return False
        
        # Validar que hay crédito suficiente
        credito_disponible = float(cliente.limite_credito - cliente.credito_usado)
        if monto > credito_disponible:
            return False
        
        # Ocupar crédito
        cliente.credito_usado = float(cliente.credito_usado) + monto
        db.commit()
        return True
    
    @staticmethod
    def liberar_credito(cliente_id: int, monto: float, db: Session) -> bool:
        """
        Libera crédito del cliente (cuando se cobran cheques).
        
        Args:
            cliente_id: ID del cliente
            monto: Monto a liberar del crédito
            db: Sesión de base de datos
            
        Returns:
            bool: True si se pudo liberar el crédito
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return False
        
        # Liberar crédito (no puede ser negativo)
        nuevo_credito_usado = max(0, float(cliente.credito_usado) - monto)
        cliente.credito_usado = nuevo_credito_usado
        db.commit()
        return True
    
    @staticmethod
    def recalcular_credito_cliente(cliente_id: int, db: Session) -> float:
        """
        Recalcula el crédito usado de un cliente basado en sus pedidos pendientes.
        Útil para corregir inconsistencias.
        
        Args:
            cliente_id: ID del cliente
            db: Sesión de base de datos
            
        Returns:
            float: Nuevo crédito usado calculado
        """
        # Obtener estado COBRADO
        estado_cobrado = db.query(EstadoCheque).filter(EstadoCheque.codigo == "COBRADO").first()
        if not estado_cobrado:
            return 0.0
        
        # Obtener pedidos diferidos no cobrados (cheque o plazo_dias > 0)
        pedidos_pendientes = db.query(Pedido).filter(
            Pedido.cliente_id == cliente_id,
            Pedido.es_pagado == False
        ).all()

        credito_usado_calculado = 0.0
        for pedido in pedidos_pendientes:
            if not pedido.medio_pago:
                continue
            es_diferido = pedido.medio_pago.permite_cheque or (pedido.medio_pago.plazo_dias or 0) > 0
            if not es_diferido:
                continue
            # Para cheques: solo contar si tienen cheques sin cobrar
            if pedido.medio_pago.permite_cheque:
                if pedido.cheques:
                    cheques_cobrados = sum(1 for c in pedido.cheques if c.estado_id == estado_cobrado.id)
                    if cheques_cobrados < len(pedido.cheques):
                        credito_usado_calculado += float(pedido.monto_total)
            else:
                # Transferencias diferidas: contar directamente
                credito_usado_calculado += float(pedido.monto_total)
        
        # Actualizar en base de datos
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if cliente:
            cliente.credito_usado = credito_usado_calculado
            db.commit()
        
        return credito_usado_calculado
    
    @staticmethod
    def obtener_info_credito(cliente_id: int, db: Session) -> Optional[dict]:
        """
        Obtiene información completa del crédito de un cliente.
        
        Args:
            cliente_id: ID del cliente
            db: Sesión de base de datos
            
        Returns:
            dict: Información del crédito o None si no existe el cliente
        """
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return None
        
        limite = float(cliente.limite_credito)
        usado = float(cliente.credito_usado)
        disponible = limite - usado
        
        return {
            "cliente_id": cliente.id,
            "cliente_nombre": cliente.nombre,
            "limite_credito": limite,
            "credito_usado": usado,
            "credito_disponible": disponible,
            "porcentaje_uso": (usado / limite * 100) if limite > 0 else 0,
            "puede_usar_credito": disponible > 0
        }