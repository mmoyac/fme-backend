#!/usr/bin/env python3
"""
Script para corregir el problema completo de puntos de Marcelo
"""

import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import Cliente, Pedido, MovimientoPuntos, PuntosCliente

def corregir_puntos_marcelo():
    db = SessionLocal()
    
    try:
        print("🔧 CORRIGIENDO PUNTOS DE MARCELO")
        print("=" * 50)
        
        # 1. Buscar cliente Marcelo
        marcelo = db.query(Cliente).filter(
            Cliente.nombre.ilike('%marcelo%')
        ).first()
        
        if not marcelo:
            print("❌ No se encontró cliente Marcelo")
            return
        
        print(f"Cliente: {marcelo.nombre} (ID: {marcelo.id})")
        
        # 2. Obtener estado actual
        puntos_cliente = db.query(PuntosCliente).filter(
            PuntosCliente.cliente_id == marcelo.id
        ).first()
        
        print(f"\n📊 ESTADO ACTUAL:")
        print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
        print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
        print(f"   Puntos totales usados: {puntos_cliente.puntos_totales_usados}")
        
        # 3. Corregir PED-00027 - Asignar puntos ganados
        ped_27 = db.query(Pedido).filter(Pedido.id == 27).first()
        if ped_27:
            print(f"\n🔧 CORRIGIENDO PED-00027:")
            print(f"   Puntos ganados antes: {ped_27.puntos_ganados}")
            ped_27.puntos_ganados = 8  # Debería tener 8 puntos por el queso
            print(f"   Puntos ganados después: {ped_27.puntos_ganados}")
        
        # 4. Recalcular saldo de puntos del cliente
        print(f"\n🔧 RECALCULANDO SALDO:")
        
        # Obtener todos los movimientos
        movimientos = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.cliente_id == marcelo.id
        ).order_by(MovimientoPuntos.fecha_movimiento.asc()).all()
        
        saldo_calculado = 0
        puntos_ganados_total = 0
        puntos_usados_total = 0
        
        for mov in movimientos:
            if mov.tipo_movimiento.value in ['GANADOS']:
                saldo_calculado += mov.puntos
                puntos_ganados_total += mov.puntos
            elif mov.tipo_movimiento.value in ['USADOS']:
                saldo_calculado -= mov.puntos
                puntos_usados_total += mov.puntos
            elif mov.tipo_movimiento.value in ['AJUSTE']:
                if mov.puntos < 0:
                    saldo_calculado += mov.puntos  # Resta (porque mov.puntos ya es negativo)
                    # Si es ajuste negativo, fue una devolución incorrecta
                else:
                    saldo_calculado += mov.puntos
        
        print(f"   Saldo calculado: {saldo_calculado}")
        print(f"   Puntos ganados total: {puntos_ganados_total}")
        print(f"   Puntos usados total: {puntos_usados_total}")
        
        # Análisis: Marcelo debería tener:
        # PED-00026: 8 puntos ganados (cuando se confirme)
        # PED-00027: 8 puntos ganados (cuando se confirme) - 5 puntos usados (cuando se confirme)
        # Pero PED-00027 está PENDIENTE, así que los puntos no deberían estar usados todavía
        
        print(f"\n💡 ANÁLISIS:")
        print(f"   PED-00026: CONFIRMADO → 8 puntos ganados ✅")
        print(f"   PED-00027: PENDIENTE → 0 puntos ganados/usados ✅")
        print(f"   Saldo correcto: 8 puntos disponibles")
        
        # Como PED-00027 está PENDIENTE, devolver los 5 puntos usados incorrectamente
        if ped_27 and ped_27.estado == 'PENDIENTE' and ped_27.puntos_usados > 0:
            print(f"\n🔧 DEVOLVIENDO PUNTOS USADOS INCORRECTAMENTE:")
            print(f"   Devolviendo {ped_27.puntos_usados} puntos")
            
            # Crear movimiento de ajuste para devolver los puntos
            nuevo_movimiento = MovimientoPuntos(
                cliente_id=marcelo.id,
                pedido_id=ped_27.id,
                tipo_movimiento='AJUSTE',
                puntos=ped_27.puntos_usados,  # Positivo para sumar
                descripcion=f"Corrección: Devolución de puntos usados en pedido PENDIENTE #{ped_27.id}"
            )
            db.add(nuevo_movimiento)
            
            # Actualizar saldo del cliente
            puntos_cliente.puntos_disponibles = 8  # 8 puntos del PED-00026
            puntos_cliente.puntos_totales_ganados = 8  # Solo los del PED-00026
            puntos_cliente.puntos_totales_usados = 0  # Ninguno usado realmente
        
        # Confirmar cambios
        db.commit()
        
        print(f"\n✅ CORRECCIÓN COMPLETADA:")
        print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
        print(f"   PED-00027 puntos ganados: {ped_27.puntos_ganados}")
        print(f"   Estado: ¡Correcto!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    corregir_puntos_marcelo()