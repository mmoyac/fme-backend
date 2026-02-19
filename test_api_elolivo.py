import requests
import json

# Login con usuario de El Olivo
login_url = "http://localhost:8000/api/auth/token"
login_data = {
    "username": "admin@elolivo.cl",
    "password": "admin"
}

# Usar header Host para simular request desde elolivo.local
headers_host = {
    "Host": "elolivo.local:8000"
}

try:
    # Login
    response = requests.post(login_url, data=login_data, headers=headers_host)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login exitoso")
        print(f"Token: {token[:50]}...")
        print()
        
        # Obtener pedidos confirmados
        pedidos_url = "http://localhost:8000/api/pedidos/?estado=CONFIRMADO"
        headers = {
            "Authorization": f"Bearer {token}",
            "Host": "elolivo.local:8000"
        }
        
        response = requests.get(pedidos_url, headers=headers)
        if response.status_code == 200:
            pedidos = response.json()
            print(f"📦 Pedidos CONFIRMADOS: {len(pedidos)}")
            print()
            
            # Filtrar sin despacho (como hace el frontend)
            sin_despacho = [p for p in pedidos if not p.get('despacho')]
            print(f"🚨 Sin despacho asignado: {len(sin_despacho)}")
            print()
            
            for pedido in pedidos:
                print(f"Pedido #{pedido['id']}:")
                print(f"  numero_pedido: {pedido.get('numero_pedido')}")
                print(f"  cliente_nombre: {pedido.get('cliente_nombre')}")
                print(f"  monto_total: {pedido.get('monto_total')}")
                print(f"  despacho: {pedido.get('despacho')}")
                print(f"  items: {len(pedido.get('items', []))} items")
                print()
        else:
            print(f"❌ Error al obtener pedidos: {response.status_code}")
            print(response.text)
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
