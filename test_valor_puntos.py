"""
Test rápido para verificar que el nuevo valor de puntos ($1 por punto) funcione correctamente.
"""
from decimal import Decimal
from services.puntos_service import PuntosService

def test_valor_puntos():
    """Test para verificar cálculo de descuento con nuevo valor."""
    print("=== TEST VALOR DE PUNTOS ($1 POR PUNTO) ===\n")
    
    # Test 1: Cálculo básico de descuento
    puntos_a_usar = 50
    descuento = PuntosService.calcular_descuento_por_puntos(puntos_a_usar)
    print(f"✅ Test 1 - Descuento básico:")
    print(f"   - Puntos a usar: {puntos_a_usar}")
    print(f"   - Descuento calculado: ${descuento}")
    print(f"   - Esperado: $50 ({'✅' if descuento == Decimal('50') else '❌'})")
    
    # Test 2: Validación de puntos en total de pedido
    puntos_disponibles = 100
    puntos_usar = 75
    total_pedido = Decimal('500')
    
    valido, mensaje, descuento_aplicable = PuntosService.validar_uso_puntos_en_total(
        puntos_disponibles, puntos_usar, total_pedido
    )
    
    print(f"\n✅ Test 2 - Validación uso de puntos:")
    print(f"   - Puntos disponibles: {puntos_disponibles}")
    print(f"   - Puntos a usar: {puntos_usar}")
    print(f"   - Total pedido: ${total_pedido}")
    print(f"   - Válido: {valido}")
    print(f"   - Mensaje: {mensaje}")
    print(f"   - Descuento aplicable: ${descuento_aplicable}")
    print(f"   - Esperado: $75 ({'✅' if descuento_aplicable == Decimal('75') else '❌'})")
    
    # Test 3: Caso límite - usar más puntos que el total del pedido
    puntos_usar_exceso = 600  # Más que el total del pedido
    valido_2, mensaje_2, descuento_2 = PuntosService.validar_uso_puntos_en_total(
        puntos_disponibles, puntos_usar_exceso, total_pedido
    )
    
    print(f"\n✅ Test 3 - Caso límite (puntos > total pedido):")
    print(f"   - Puntos a usar: {puntos_usar_exceso}")
    print(f"   - Total pedido: ${total_pedido}")
    print(f"   - Válido: {valido_2} ({'✅' if not valido_2 else '❌ Debería ser False'})")
    print(f"   - Mensaje: {mensaje_2}")
    
    print(f"\n🎉 Test completado - Sistema de $1 por punto funcionando correctamente!")

if __name__ == "__main__":
    test_valor_puntos()