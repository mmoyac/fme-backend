"""
Script de prueba para el sistema de puntos.
"""
from database.database import get_db
from database.models import Cliente, Producto, Pedido, ItemPedido, CategoriaProducto
from services.puntos_service import PuntosService
from decimal import Decimal


def test_sistema_puntos():
    """Prueba completa del sistema de puntos."""
    db = next(get_db())
    
    print("=== PRUEBA DEL SISTEMA DE PUNTOS ===\n")
    
    # 1. Buscar un cliente de prueba
    cliente = db.query(Cliente).first()
    if not cliente:
        print("❌ No hay clientes en la base de datos")
        return
    
    print(f"👤 Cliente de prueba: {cliente.nombre} ({cliente.email})")
    
    # 2. Obtener puntos actuales del cliente
    puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
    print(f"📊 Puntos actuales: {puntos_cliente.puntos_disponibles}")
    
    # 3. Buscar productos de diferentes categorías
    productos_con_categoria = (
        db.query(Producto)
        .join(CategoriaProducto, Producto.categoria_id == CategoriaProducto.id)
        .filter(CategoriaProducto.puntos_fidelidad > 0)
        .limit(3)
        .all()
    )
    
    if not productos_con_categoria:
        print("❌ No hay productos con categorías que otorguen puntos")
        return
    
    print(f"\n🛍️ Productos con puntos encontrados:")
    for prod in productos_con_categoria:
        print(f"  - {prod.nombre} ({prod.categoria.nombre}): {prod.categoria.puntos_fidelidad} puntos por unidad")
    
    # 4. Crear un pedido simulado (sin guardar en DB)
    print(f"\n📦 Simulando pedido con productos:")
    total_puntos_esperados = 0
    for prod in productos_con_categoria:
        cantidad = 2  # Comprar 2 unidades de cada producto
        puntos_producto = prod.categoria.puntos_fidelidad * cantidad
        total_puntos_esperados += puntos_producto
        print(f"  - {cantidad}x {prod.nombre}: {puntos_producto} puntos")
    
    print(f"\n🎯 Total puntos esperados: {total_puntos_esperados}")
    
    # 5. Probar validación de uso de puntos
    print(f"\n💰 Probando validación de uso de puntos:")
    total_pedido = Decimal('5000')  # $5000 de pedido
    puntos_a_usar = min(puntos_cliente.puntos_disponibles, 50)  # Usar máximo 50 puntos
    
    if puntos_a_usar > 0:
        valido, mensaje, descuento = PuntosService.validar_uso_puntos_en_total(
            puntos_cliente.puntos_disponibles,
            puntos_a_usar,
            total_pedido
        )
        
        print(f"  - Usar {puntos_a_usar} puntos en pedido de ${total_pedido:,.0f}")
        print(f"  - ✅ Válido: {valido}")
        print(f"  - 💸 Descuento: ${descuento:,.0f}")
        print(f"  - 📝 Mensaje: {mensaje}")
    else:
        print("  - ⚠️ Cliente no tiene puntos para usar")
    
    # 6. Mostrar estadísticas generales
    print(f"\n📈 Estadísticas del sistema:")
    try:
        stats = PuntosService.obtener_estadisticas_puntos(db)
        print(f"  - Total puntos ganados: {stats['total_ganados']:,}")
        print(f"  - Total puntos usados: {stats['total_usados']:,}")
        print(f"  - Total puntos disponibles: {stats['total_disponibles']:,}")
        print(f"  - Clientes con puntos: {stats['clientes_con_puntos']}")
    except Exception as e:
        print(f"  - ❌ Error al obtener estadísticas: {e}")
    
    print(f"\n✅ Prueba del sistema de puntos completada!")


if __name__ == "__main__":
    test_sistema_puntos()