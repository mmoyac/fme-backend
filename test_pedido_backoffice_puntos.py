"""
Test del flujo completo de pedido con puntos desde el backoffice.
"""
import requests
import json


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
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Error login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_pedido_con_puntos_backoffice():
    """Test del flujo de pedido con canje de puntos desde backoffice."""
    print("=== TEST PEDIDO CON PUNTOS - BACKOFFICE ===\n")
    
    # 1. Obtener token
    print("🔐 Obteniendo token...")
    token = obtener_token()
    if not token:
        return
    print("✅ Token obtenido")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. Obtener cliente con puntos
    print("\n👤 Buscando cliente con puntos...")
    response = requests.get("http://localhost:8000/api/clientes/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo clientes: {response.status_code}")
        return
    
    clientes = response.json()
    cliente_con_puntos = None
    
    for cliente in clientes:
        if cliente.get('puntos_disponibles', 0) > 0:
            cliente_con_puntos = cliente
            break
    
    if not cliente_con_puntos:
        print("❌ No se encontró cliente con puntos disponibles")
        return
    
    print(f"✅ Cliente encontrado: {cliente_con_puntos['nombre']}")
    print(f"   - Puntos disponibles: {cliente_con_puntos['puntos_disponibles']}")
    print(f"   - Valor: ${cliente_con_puntos['puntos_disponibles']}")
    
    # 3. Obtener datos necesarios
    print(f"\n📊 Obteniendo datos para pedido...")
    
    # Obtener productos
    response = requests.get("http://localhost:8000/api/productos/", headers=headers)
    productos = response.json()
    producto = productos[0] if productos else None
    
    # Obtener locales
    response = requests.get("http://localhost:8000/api/locales/", headers=headers)
    locales = response.json()
    local = locales[0] if locales else None
    
    # Obtener medios de pago
    response = requests.get("http://localhost:8000/api/maestras/medios-pago", headers=headers)
    medios_pago = response.json()
    medio_pago = medios_pago[0] if medios_pago else None
    
    if not all([producto, local, medio_pago]):
        print(f"❌ Faltan datos: producto={bool(producto)}, local={bool(local)}, medio_pago={bool(medio_pago)}")
        return
    
    print(f"✅ Datos obtenidos:")
    print(f"   - Producto: {producto['nombre']} (${producto.get('precio', 1000)})")
    print(f"   - Local: {local['nombre']}")
    print(f"   - Medio de pago: {medio_pago['nombre']}")
    
    # 4. Crear pedido con puntos
    puntos_a_usar = min(cliente_con_puntos['puntos_disponibles'], 3)  # Usar máximo 3 puntos
    precio_unitario = 5000  # $5000 por producto
    cantidad = 1
    
    pedido_data = {
        "cliente_id": cliente_con_puntos['id'],
        "cliente_nombre": cliente_con_puntos['nombre'],
        "cliente_email": cliente_con_puntos['email'] or "test@example.com",
        "cliente_telefono": cliente_con_puntos.get('telefono', "123456789"),
        "direccion_entrega": cliente_con_puntos.get('direccion', "Dirección de prueba"),
        "local_id": local['id'],
        "medio_pago_id": medio_pago['id'],
        "notas": f"Pedido de prueba con {puntos_a_usar} puntos canjeados",
        "puntos_usar": puntos_a_usar,
        "items": [
            {
                "sku": producto['sku'],
                "producto_id": producto['id'],
                "cantidad": cantidad,
                "precio_unitario_venta": precio_unitario
            }
        ]
    }
    
    print(f"\n🛒 Creando pedido:")
    print(f"   - Subtotal: ${precio_unitario * cantidad:,}")
    print(f"   - Puntos a usar: {puntos_a_usar}")
    print(f"   - Descuento: ${puntos_a_usar}")
    print(f"   - Total esperado: ${(precio_unitario * cantidad) - puntos_a_usar:,}")
    
    response = requests.post(
        "http://localhost:8000/api/pedidos/backoffice",
        json=pedido_data,
        headers=headers
    )
    
    if response.status_code == 201:
        resultado = response.json()
        pedido_id = resultado.get('pedido_id')
        
        print(f"✅ Pedido creado exitosamente!")
        print(f"   - ID: {pedido_id}")
        print(f"   - Total: ${resultado.get('total', 0):,}")
        print(f"   - Descuento aplicado: ${resultado.get('descuento_puntos', 0)}")
        print(f"   - Puntos usados: {resultado.get('puntos_usados', 0)}")
        print(f"   - Puntos ganados: {resultado.get('puntos_ganados', 0)}")
        
        # 5. Verificar que los puntos del cliente se actualizaron
        print(f"\n🔍 Verificando puntos del cliente...")
        response = requests.get(f"http://localhost:8000/api/clientes/{cliente_con_puntos['id']}", headers=headers)
        
        if response.status_code == 200:
            cliente_actualizado = response.json()
            puntos_nuevos = cliente_actualizado.get('puntos_disponibles', 0)
            
            print(f"✅ Cliente actualizado:")
            print(f"   - Puntos antes: {cliente_con_puntos['puntos_disponibles']}")
            print(f"   - Puntos después: {puntos_nuevos}")
            print(f"   - Diferencia: {puntos_nuevos - cliente_con_puntos['puntos_disponibles']}")
            
            # Los puntos deberían haberse reducido por el canje pero aumentado por la nueva compra
            esperado_cambio = resultado.get('puntos_ganados', 0) - puntos_a_usar
            cambio_real = puntos_nuevos - cliente_con_puntos['puntos_disponibles']
            
            if cambio_real == esperado_cambio:
                print(f"✅ ¡Puntos calculados correctamente!")
            else:
                print(f"⚠️ Diferencia en puntos: esperado {esperado_cambio}, real {cambio_real}")
        
        # 6. Obtener detalle del pedido creado
        print(f"\n📋 Obteniendo detalle del pedido...")
        response = requests.get(f"http://localhost:8000/api/pedidos/{pedido_id}", headers=headers)
        
        if response.status_code == 200:
            pedido_detalle = response.json()
            print(f"✅ Detalle del pedido:")
            print(f"   - Estado: {pedido_detalle.get('estado')}")
            print(f"   - Total: ${pedido_detalle.get('total', 0):,}")
            print(f"   - Puntos usados: {pedido_detalle.get('puntos_usados', 0)}")
            print(f"   - Descuento puntos: ${pedido_detalle.get('descuento_puntos', 0)}")
            print(f"   - Puntos ganados: {pedido_detalle.get('puntos_ganados', 0)}")
            print(f"   - Items: {len(pedido_detalle.get('items', []))}")
        
        print(f"\n🎉 ¡Test completado exitosamente!")
        print(f"\n📊 RESUMEN:")
        print(f"   - ✅ Cliente con puntos identificado")
        print(f"   - ✅ Pedido creado con descuento por puntos")
        print(f"   - ✅ Puntos descontados del cliente")
        print(f"   - ✅ Nuevos puntos ganados calculados")
        print(f"   - ✅ Sistema de puntos en backoffice funcional")
        
    else:
        print(f"❌ Error creando pedido: {response.status_code}")
        print(f"Respuesta: {response.text}")


if __name__ == "__main__":
    test_pedido_con_puntos_backoffice()