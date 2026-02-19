import requests
import json

# Test endpoint de pedidos
url = "http://localhost:8001/api/pedidos/"

# Obtener token de admin
login_data = {
    "username": "admin@eolivo.cl",
    "password": "admin"
}

login_response = requests.post("http://localhost:8001/api/auth/login", data=login_data)
token = login_response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

# Obtener pedidos
response = requests.get(url, headers=headers)
pedidos = response.json()

# Buscar pedido 79
pedido_79 = None
for p in pedidos:
    if p['id'] == 79:
        pedido_79 = p
        break

if pedido_79:
    print("✅ Pedido #79 encontrado:")
    print(f"  ID: {pedido_79.get('id')}")
    print(f"  cliente_nombre: {pedido_79.get('cliente_nombre')}")
    print(f"  monto_total: {pedido_79.get('monto_total')}")
    print(f"  total: {pedido_79.get('total')}")
    print(f"  cliente_id: {pedido_79.get('cliente_id')}")
    print(f"  numero_pedido: {pedido_79.get('numero_pedido')}")
    print("\n📋 Estructura completa:")
    print(json.dumps(pedido_79, indent=2, default=str))
else:
    print("❌ Pedido #79 no encontrado")
    print(f"\nTotal pedidos: {len(pedidos)}")
