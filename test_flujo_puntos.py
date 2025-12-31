"""
Test completo del sistema de puntos con pedidos reales.
"""
from database.database import get_db
from database.models import *
from services.puntos_service import PuntosService
from decimal import Decimal
import json


def test_flujo_completo_puntos():
    """Test del flujo completo: crear pedido → confirmar → ganar puntos → usar puntos."""
    db = next(get_db())
    
    print("=== FLUJO COMPLETO DEL SISTEMA DE PUNTOS ===\n")
    
    # 1. Buscar cliente y productos
    cliente = db.query(Cliente).first()
    local_web = db.query(Local).filter(Local.codigo == 'WEB').first()
    
    productos = (
        db.query(Producto)
        .join(CategoriaProducto, Producto.categoria_id == CategoriaProducto.id)
        .join(Precio, Producto.id == Precio.producto_id)
        .filter(
            Precio.local_id == local_web.id,
            CategoriaProducto.puntos_fidelidad > 0
        )
        .limit(2)
        .all()
    )
    
    if not productos:
        print("❌ No hay productos con precios y categorías con puntos")
        return
    
    print(f"👤 Cliente: {cliente.nombre}")
    print(f"🏪 Local WEB ID: {local_web.id}")
    print(f"🛍️ Productos seleccionados:")
    for prod in productos:
        precio = next((p for p in prod.precios if p.local_id == local_web.id), None)
        print(f"  - {prod.nombre} (${precio.monto_precio:,.0f}) - Categoría: {prod.categoria.nombre} ({prod.categoria.puntos_fidelidad} pts/unidad)")
    
    # 2. Simular creación de pedido (como haría el endpoint)
    print(f"\n📦 PASO 1: Crear pedido...")
    
    # Calcular total y puntos esperados
    monto_total = 0.0
    puntos_esperados = 0
    
    for prod in productos:
        precio = next((p for p in prod.precios if p.local_id == local_web.id), None)
        cantidad = 2
        monto_total += precio.monto_precio * cantidad
        puntos_esperados += prod.categoria.puntos_fidelidad * cantidad
    
    # Crear pedido simulado
    pedido = Pedido(
        cliente_id=cliente.id,
        local_id=local_web.id,
        monto_total=monto_total,
        estado="PENDIENTE",
        es_pagado=False,
        puntos_ganados=puntos_esperados,  # Se calcularía en el endpoint
        puntos_usados=0,
        descuento_puntos=0
    )
    db.add(pedido)
    db.flush()
    
    # Crear items del pedido
    for prod in productos:
        precio = next((p for p in prod.precios if p.local_id == local_web.id), None)
        item = ItemPedido(
            pedido_id=pedido.id,
            producto_id=prod.id,
            cantidad=2,
            precio_unitario_venta=precio.monto_precio
        )
        db.add(item)
    
    db.commit()
    db.refresh(pedido)
    
    print(f"✅ Pedido {pedido.id} creado")
    print(f"💰 Total: ${monto_total:,.0f}")
    print(f"🎯 Puntos a ganar: {puntos_esperados}")
    
    # 3. Verificar cálculo de puntos
    print(f"\n📊 PASO 2: Verificar cálculo de puntos...")
    
    puntos_calculados = PuntosService.calcular_puntos_por_pedido(db, pedido.id)
    print(f"✅ Puntos calculados por servicio: {puntos_calculados}")
    
    assert puntos_calculados == puntos_esperados, f"Mismatch en puntos: {puntos_calculados} != {puntos_esperados}"
    
    # 4. Confirmar pedido y otorgar puntos
    print(f"\n✅ PASO 3: Confirmar pedido y otorgar puntos...")
    
    # Obtener local de despacho (primer local físico)
    local_fisico = db.query(Local).filter(Local.codigo != 'WEB').first()
    
    # Simular confirmación
    pedido.estado = "CONFIRMADO"
    pedido.local_despacho_id = local_fisico.id
    
    # Otorgar puntos (como haría el endpoint)
    movimiento = PuntosService.otorgar_puntos_por_pedido(
        db, cliente.id, pedido.id, puntos_esperados,
        f"Puntos ganados por confirmación de pedido #{pedido.id}"
    )
    
    db.commit()
    
    print(f"✅ Pedido confirmado")
    print(f"🎁 Puntos otorgados: {puntos_esperados}")
    
    # 5. Verificar puntos del cliente
    puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
    print(f"📊 Puntos disponibles del cliente: {puntos_cliente.puntos_disponibles}")
    
    # 6. Crear segundo pedido usando puntos
    print(f"\n💳 PASO 4: Crear segundo pedido usando puntos...")
    
    puntos_a_usar = min(puntos_cliente.puntos_disponibles, 30)  # Usar hasta 30 puntos
    segundo_total = 1000.0  # $1000
    
    if puntos_a_usar > 0:
        # Validar uso de puntos
        valido, mensaje, descuento = PuntosService.validar_uso_puntos_en_total(
            puntos_cliente.puntos_disponibles,
            puntos_a_usar,
            Decimal(str(segundo_total))
        )
        
        print(f"🔍 Validación de {puntos_a_usar} puntos en pedido de ${segundo_total:,.0f}:")
        print(f"  - Válido: {valido}")
        print(f"  - Descuento: ${descuento:,.0f}")
        print(f"  - Mensaje: {mensaje}")
        
        if valido:
            # Crear segundo pedido
            segundo_pedido = Pedido(
                cliente_id=cliente.id,
                local_id=local_web.id,
                monto_total=segundo_total - float(descuento),
                estado="PENDIENTE",
                es_pagado=False,
                puntos_ganados=0,  # Por simplicidad, no agregamos más productos
                puntos_usados=puntos_a_usar,
                descuento_puntos=float(descuento)
            )
            db.add(segundo_pedido)
            db.flush()
            
            # Usar puntos
            exito, mensaje_uso, movimiento_uso = PuntosService.usar_puntos_en_pedido(
                db, cliente.id, segundo_pedido.id, puntos_a_usar, descuento
            )
            
            db.commit()
            
            print(f"✅ Segundo pedido creado: ${segundo_pedido.monto_total:,.0f} (después de descuento)")
            print(f"💸 Puntos usados: {puntos_a_usar}")
            
            # Verificar puntos restantes
            puntos_final = PuntosService.obtener_puntos_cliente(db, cliente.id)
            print(f"📊 Puntos restantes: {puntos_final.puntos_disponibles}")
    
    # 7. Mostrar historial de movimientos
    print(f"\n📜 PASO 5: Historial de puntos del cliente...")
    historial = PuntosService.obtener_historial_puntos(db, cliente.id, limite=10)
    
    for mov in historial:
        tipo_emoji = "🎁" if mov.tipo_movimiento == "GANANCIA" else "💸"
        print(f"  {tipo_emoji} {mov.fecha_movimiento.strftime('%Y-%m-%d %H:%M')} - {mov.tipo_movimiento}: {mov.puntos} pts - {mov.descripcion}")
    
    # 8. Estadísticas finales
    print(f"\n📈 ESTADÍSTICAS FINALES:")
    stats = PuntosService.obtener_estadisticas_puntos(db)
    print(f"  - Total ganados: {stats['total_ganados']:,}")
    print(f"  - Total usados: {stats['total_usados']:,}")
    print(f"  - Total disponibles: {stats['total_disponibles']:,}")
    print(f"  - Clientes con puntos: {stats['clientes_con_puntos']}")
    
    print(f"\n🎉 ¡Flujo completo del sistema de puntos exitoso!")
    print(f"📊 Resumen:")
    print(f"  - Pedido 1: ${monto_total:,.0f} → {puntos_esperados} puntos ganados")
    if puntos_a_usar > 0:
        print(f"  - Pedido 2: ${segundo_total:,.0f} → {puntos_a_usar} puntos usados (${descuento:,.0f} descuento)")
    
    # Limpiar test (opcional)
    # db.delete(segundo_pedido)
    # db.delete(pedido) 
    # db.commit()


if __name__ == "__main__":
    test_flujo_completo_puntos()