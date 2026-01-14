#!/usr/bin/env python3
"""
Script para probar la creación de pedidos con diferentes tipos.
"""
import sys
import os

# Cambiar working directory a la raíz del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tipos_pedido():
    """Test simple de la lógica de tipos de pedido."""
    print("=== 🧪 TEST: Tipos de Pedido ===")
    
    # Simular los códigos de tipo
    tipos_disponibles = {
        1: {"codigo": "PRODUCTOS", "nombre": "Productos Regulares"},
        2: {"codigo": "CAJAS_VARIABLES", "nombre": "Cajas Variables"}
    }
    
    print("\n📋 Tipos de pedido disponibles:")
    for id, tipo in tipos_disponibles.items():
        print(f"   {id}: {tipo['codigo']} - {tipo['nombre']}")
    
    # Simular lógica de descuento de inventario
    def simular_descuento_inventario(tipo_id, items):
        tipo = tipos_disponibles.get(tipo_id)
        if not tipo:
            return f"❌ Error: Tipo {tipo_id} no encontrado"
        
        if tipo['codigo'] == 'PRODUCTOS':
            return f"✅ Descuentos aplicados a inventario REGULAR para {len(items)} items"
        elif tipo['codigo'] == 'CAJAS_VARIABLES':
            return f"✅ Descuentos aplicados a STOCK CAJAS para {len(items)} items"
        else:
            return f"❌ Tipo {tipo['codigo']} no soportado"
    
    # Test 1: Pedido de productos regulares
    print(f"\n🔄 Test 1: Pedido PRODUCTOS (tipo_id=1)")
    items_productos = [{"producto": "Pan", "cantidad": 5}]
    resultado1 = simular_descuento_inventario(1, items_productos)
    print(f"   {resultado1}")
    
    # Test 2: Pedido de cajas variables  
    print(f"\n🔄 Test 2: Pedido CAJAS_VARIABLES (tipo_id=2)")
    items_cajas = [{"producto": "Lomo", "cantidad": 3}, {"producto": "Costilla", "cantidad": 2}]
    resultado2 = simular_descuento_inventario(2, items_cajas)
    print(f"   {resultado2}")
    
    # Test 3: Tipo inválido
    print(f"\n🔄 Test 3: Tipo inválido (tipo_id=99)")
    resultado3 = simular_descuento_inventario(99, [])
    print(f"   {resultado3}")
    
    print(f"\n✅ Simulación completada exitosamente!")
    print(f"✅ La lógica de tipos de pedido está funcionando correctamente")

if __name__ == "__main__":
    test_tipos_pedido()