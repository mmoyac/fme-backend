#!/usr/bin/env python3
"""
Script para investigar el pedido PED-00026 y verificar el estado de los puntos.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session, sessionmaker
from database.database import engine
from database.models import Pedido, MovimientoPuntos, PuntosCliente, Cliente, ItemPedido, Producto
from services.puntos_service import PuntosService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def investigar_pedido_26():
    db: Session = SessionLocal()
    
    try:
        print("=== 🔍 INVESTIGACIÓN: Pedido PED-00026 ===")
        
        # 1. Buscar pedido 26
        pedido = db.query(Pedido).filter(Pedido.id == 26).first()
        if not pedido:
            print("❌ No se encontró pedido con ID 26")
            return
        
        cliente = pedido.cliente
        
        print(f"📋 Información del Pedido:")
        print(f"   ID: {pedido.id}")
        print(f"   Número: PED-{pedido.id:05d}")
        print(f"   Cliente: {cliente.nombre} - {cliente.email}")
        print(f"   Estado: {pedido.estado}")
        print(f"   Total: ${pedido.monto_total}")
        print(f"   Puntos ganados registrados: {pedido.puntos_ganados}")
        print(f"   Puntos usados: {pedido.puntos_usados}")
        print(f"   Descuento puntos: ${pedido.descuento_puntos}")
        print(f"   Fecha: {pedido.fecha_pedido}")
        
        # 2. Ver items del pedido
        items = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido.id).all()
        print(f"\n📦 Items del pedido:")
        for item in items:
            producto = item.producto
            categoria = producto.categoria if producto else None
            print(f"   - {producto.nombre if producto else 'Producto desconocido'}")
            print(f"     Cantidad: {item.cantidad}")
            print(f"     Precio unitario: ${item.precio_unitario_venta}")
            print(f"     Categoría: {categoria.nombre if categoria else 'Sin categoría'}")
            print(f"     Puntos categoría: {categoria.puntos_fidelidad if categoria else 0}")
        
        # 3. Verificar cálculo de puntos actual
        puntos_calculados_ahora = PuntosService.calcular_puntos_por_pedido(db, pedido.id)
        print(f"\n🧮 Verificación de cálculo:")
        print(f"   Puntos registrados en pedido: {pedido.puntos_ganados}")
        print(f"   Puntos calculados ahora: {puntos_calculados_ahora}")
        
        # 4. Ver estado de puntos del cliente
        puntos_cliente = db.query(PuntosCliente).filter(PuntosCliente.cliente_id == cliente.id).first()
        if puntos_cliente:
            print(f"\n💰 Estado de puntos del cliente:")
            print(f"   Puntos disponibles: {puntos_cliente.puntos_disponibles}")
            print(f"   Puntos totales ganados: {puntos_cliente.puntos_totales_ganados}")
            print(f"   Puntos totales usados: {puntos_cliente.puntos_totales_usados}")
        else:
            print(f"\n❌ No hay registro de puntos para este cliente")
        
        # 5. Ver movimientos de puntos relacionados con este pedido
        movimientos = db.query(MovimientoPuntos).filter(MovimientoPuntos.pedido_id == pedido.id).all()
        print(f"\n📊 Movimientos de puntos para este pedido ({len(movimientos)}):")
        for mov in movimientos:
            print(f"   - {mov.tipo_movimiento.value}: {mov.puntos} puntos")
            print(f"     Fecha: {mov.fecha_movimiento}")
            print(f"     Descripción: {mov.descripcion}")
        
        # 6. Diagnóstico
        print(f"\n🔬 DIAGNÓSTICO:")
        
        if pedido.estado == 'CONFIRMADO':
            print(f"   ✅ El pedido está CONFIRMADO")
            
            if pedido.puntos_ganados and pedido.puntos_ganados > 0:
                print(f"   ✅ Tiene puntos ganados calculados: {pedido.puntos_ganados}")
                
                if len(movimientos) > 0:
                    mov_ganados = [m for m in movimientos if m.tipo_movimiento.value == 'GANADOS']
                    if mov_ganados:
                        print(f"   ✅ Se encontraron {len(mov_ganados)} movimientos de puntos ganados")
                    else:
                        print(f"   ❌ NO se encontraron movimientos de puntos ganados")
                        print(f"       Esto indica que la función de otorgar puntos no se ejecutó correctamente")
                else:
                    print(f"   ❌ NO hay movimientos de puntos para este pedido")
                    print(f"       Esto indica que la función de otorgar puntos no se ejecutó")
            else:
                print(f"   ❌ No tiene puntos ganados calculados")
        else:
            print(f"   ❌ El pedido no está CONFIRMADO, estado actual: {pedido.estado}")
        
        print(f"\n✅ Investigación completada")
        
    except Exception as e:
        print(f"❌ Error durante investigación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    investigar_pedido_26()