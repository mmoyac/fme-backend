"""
Test para encontrar el pedido específico que generó 60 puntos.
"""
import requests


def obtener_token():
    """Obtiene token de autenticación."""
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/token", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token") if response.status_code == 200 else None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def encontrar_pedido_60_puntos():
    """Encontrar el pedido que generó exactamente 60 puntos."""
    print("=== BÚSQUEDA: PEDIDO QUE GENERÓ 60 PUNTOS ===\n")
    
    token = obtener_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. Obtener todos los pedidos recientes
    print("📋 Obteniendo pedidos recientes...")
    response = requests.get("http://localhost:8000/api/pedidos/", headers=headers)
    
    if response.status_code == 200:
        pedidos = response.json()
        print(f"✅ {len(pedidos)} pedidos encontrados\n")
        
        for pedido in pedidos[-10:]:  # Últimos 10 pedidos
            pedido_id = pedido.get('id')
            total = pedido.get('total', 0)
            puntos_ganados = pedido.get('puntos_ganados', 0)
            estado = pedido.get('estado')
            
            print(f"📦 Pedido #{pedido_id}:")
            print(f"   - Total: ${total:,.0f}")
            print(f"   - Puntos ganados: {puntos_ganados}")
            print(f"   - Estado: {estado}")
            
            if puntos_ganados == 60:
                print(f"   🎯 ¡ENCONTRADO! Este pedido generó 60 puntos")
                
                # Obtener detalle completo del pedido
                detalle_response = requests.get(f"http://localhost:8000/api/pedidos/{pedido_id}", headers=headers)
                
                if detalle_response.status_code == 200:
                    detalle = detalle_response.json()
                    items = detalle.get('items', [])
                    
                    print(f"   📊 ANÁLISIS DETALLADO:")
                    print(f"   - Número de items: {len(items)}")
                    
                    total_puntos_calculados = 0
                    
                    for i, item in enumerate(items, 1):
                        producto = item.get('producto', {})
                        cantidad = item.get('cantidad', 0)
                        precio = item.get('precio_unitario_venta', 0)
                        producto_id = producto.get('id')
                        
                        print(f"\n      Item #{i}:")
                        print(f"      - Producto: {producto.get('nombre', 'N/A')}")
                        print(f"      - SKU: {producto.get('sku', 'N/A')}")
                        print(f"      - Cantidad: {cantidad}")
                        print(f"      - Precio unitario: ${precio:,.0f}")
                        print(f"      - Subtotal: ${precio * cantidad:,.0f}")
                        
                        # Obtener categoría del producto
                        if producto_id:
                            prod_response = requests.get(f"http://localhost:8000/api/productos/{producto_id}", headers=headers)
                            
                            if prod_response.status_code == 200:
                                prod_detalle = prod_response.json()
                                categoria_id = prod_detalle.get('categoria_id')
                                
                                if categoria_id:
                                    cat_response = requests.get(f"http://localhost:8000/api/maestras/categorias/{categoria_id}", headers=headers)
                                    
                                    if cat_response.status_code == 200:
                                        categoria = cat_response.json()
                                        puntos_categoria = categoria.get('puntos_fidelidad', 0)
                                        puntos_item = puntos_categoria * cantidad
                                        total_puntos_calculados += puntos_item
                                        
                                        print(f"      - Categoría: {categoria.get('nombre')}")
                                        print(f"      - Puntos por unidad: {puntos_categoria}")
                                        print(f"      - Puntos por este item: {puntos_categoria} × {cantidad} = {puntos_item}")
                                        
                                        if puntos_item == 60 and cantidad == 1:
                                            print(f"      🚨 PROBLEMA: Esta categoría tiene {puntos_categoria} puntos, no 8!")
                                        elif puntos_item == 60 and cantidad > 1:
                                            print(f"      🤔 POSIBLE: {cantidad} productos × {puntos_categoria} = 60 puntos")
                    
                    print(f"\n   📊 RESUMEN DEL CÁLCULO:")
                    print(f"   - Total puntos calculados manualmente: {total_puntos_calculados}")
                    print(f"   - Puntos registrados en pedido: {puntos_ganados}")
                    
                    if total_puntos_calculados == puntos_ganados:
                        print(f"   ✅ Los cálculos coinciden")
                    else:
                        print(f"   ❌ DISCREPANCIA: {abs(total_puntos_calculados - puntos_ganados)} puntos de diferencia")
                    
                    if puntos_ganados == 60 and total_puntos_calculados != 60:
                        print(f"   🔧 NECESITA INVESTIGACIÓN: Los puntos no cuadran con las categorías")
                
                break
            print()
    
    else:
        print(f"❌ Error obteniendo pedidos: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    encontrar_pedido_60_puntos()