"""
Test para investigar por qué un queso de $6000 está dando 60 puntos en lugar de 8.
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


def investigar_producto_queso():
    """Investigar el cálculo de puntos para un producto específico."""
    print("=== INVESTIGACIÓN: QUESO DE $6000 → 60 PUNTOS ===\n")
    
    token = obtener_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. Buscar productos relacionados con queso
    print("🧀 Buscando productos tipo 'queso'...")
    response = requests.get("http://localhost:8000/api/productos/", headers=headers)
    
    if response.status_code == 200:
        productos = response.json()
        productos_queso = []
        
        for producto in productos:
            nombre = producto.get('nombre', '').lower()
            if 'queso' in nombre or 'lácteo' in nombre or 'lacteo' in nombre:
                productos_queso.append(producto)
        
        print(f"✅ Encontrados {len(productos_queso)} productos tipo queso\n")
        
        for producto in productos_queso:
            print(f"📦 {producto.get('nombre')} (SKU: {producto.get('sku')})")
            print(f"   - ID: {producto.get('id')}")
            print(f"   - Categoría ID: {producto.get('categoria_id', 'N/A')}")
            print(f"   - Descripción: {producto.get('descripcion', 'N/A')}")
            
            # Obtener precio de este producto en local WEB
            if producto.get('id'):
                precio_response = requests.get(
                    f"http://localhost:8000/api/precios/producto/{producto['id']}/local/1", 
                    headers=headers
                )
                
                if precio_response.status_code == 200:
                    precio = precio_response.json().get('monto_precio', 0)
                    print(f"   - Precio en WEB: ${precio:,.0f}")
                    
                    if abs(precio - 6000) < 100:  # Si el precio está cerca de $6000
                        print(f"   🎯 ¡ESTE PODRÍA SER EL PRODUCTO!")
                        
                        # Verificar la categoría
                        if producto.get('categoria_id'):
                            cat_response = requests.get(
                                f"http://localhost:8000/api/maestras/categorias/{producto['categoria_id']}", 
                                headers=headers
                            )
                            
                            if cat_response.status_code == 200:
                                categoria = cat_response.json()
                                print(f"   📂 Categoría: {categoria.get('nombre')}")
                                print(f"   🔢 Puntos por categoría: {categoria.get('puntos_fidelidad', 0)}")
                                
                                # Hacer un pedido de prueba para ver el cálculo
                                print(f"\n🧮 SIMULANDO CÁLCULO DE PUNTOS:")
                                print(f"   - Producto: {producto.get('nombre')}")
                                print(f"   - Categoría: {categoria.get('nombre')} ({categoria.get('puntos_fidelidad', 0)} pts)")
                                print(f"   - Cantidad: 1")
                                print(f"   - Puntos esperados: {categoria.get('puntos_fidelidad', 0)} × 1 = {categoria.get('puntos_fidelidad', 0)} puntos")
                                
                                if categoria.get('puntos_fidelidad', 0) == 60:
                                    print(f"   ❌ PROBLEMA ENCONTRADO: La categoría {categoria.get('nombre')} tiene 60 puntos en lugar de 8")
                                elif categoria.get('puntos_fidelidad', 0) == 8:
                                    print(f"   ✅ Categoría correcta, el problema debe estar en otro lugar")
                                
                else:
                    print(f"   ⚠️ No se pudo obtener precio")
            print()
    
    # 2. Revisar el historial de movimientos de puntos más reciente
    print("📊 Revisando historial de movimientos de puntos...")
    response = requests.get("http://localhost:8000/api/puntos/historial?limite=5", headers=headers)
    
    if response.status_code == 200:
        movimientos = response.json().get('movimientos', [])
        
        for mov in movimientos:
            if mov.get('tipo_movimiento') == 'GANADOS':
                print(f"\n💰 Movimiento reciente:")
                print(f"   - Cliente ID: {mov.get('cliente_id')}")
                print(f"   - Puntos: {mov.get('puntos')}")
                print(f"   - Pedido ID: {mov.get('pedido_id')}")
                print(f"   - Fecha: {mov.get('fecha_movimiento')}")
                print(f"   - Descripción: {mov.get('descripcion', 'N/A')}")
                
                # Si son 60 puntos, investigar más
                if mov.get('puntos') == 60:
                    print(f"   🎯 ¡ESTE ES EL MOVIMIENTO DE 60 PUNTOS!")
                    
                    # Obtener detalle del pedido
                    if mov.get('pedido_id'):
                        pedido_response = requests.get(
                            f"http://localhost:8000/api/pedidos/{mov.get('pedido_id')}", 
                            headers=headers
                        )
                        
                        if pedido_response.status_code == 200:
                            pedido = pedido_response.json()
                            print(f"   📋 Pedido #{pedido.get('id')}:")
                            print(f"   - Total: ${pedido.get('total', 0):,.0f}")
                            print(f"   - Items: {len(pedido.get('items', []))}")
                            
                            for item in pedido.get('items', []):
                                print(f"      - {item.get('cantidad')}x {item.get('producto', {}).get('nombre', 'N/A')}")
                                print(f"        SKU: {item.get('producto', {}).get('sku', 'N/A')}")
                                print(f"        Precio: ${item.get('precio_unitario_venta', 0):,.0f}")


if __name__ == "__main__":
    investigar_producto_queso()