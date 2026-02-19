"""Script para crear un pedido de prueba rápido."""
import requests
import json
from datetime import datetime

# Autenticación
BASE_URL = "http://localhost:8000"  # Dentro del contenedor
login_response = requests.post(
    f"{BASE_URL}/api/auth/token",
    data={"username": "admin@elolivo.cl", "password": "admin"}
)

if login_response.status_code != 200:
    print(f"❌ Error login: {login_response.status_code}")
    print(f"   Response: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Crear pedido
pedido_data = {
    "cliente_id": 43,  # Marcelo
    "items": [
        {
            "producto_id": 147,  # Punta Picana
            "cantidad": 2,
            "precio_unitario": 5000
        }
    ],
    "tipo_pedido_id": 2,
    "local_despacho_id": 13,
    "direccion_entrega": "Calle Prueba 123"
}

pedido = requests.post(
    f"{BASE_URL}/api/pedidos/",
    json=pedido_data,
    headers=headers
).json()

print(f"✅ Pedido creado: {pedido['numero_pedido']}")
print(f"   ID: {pedido['id']}")
print(f"   Estado: {pedido['estado_nombre']}")
print(f"   Total estimado: ${pedido['total']}")

# Confirmar pedido
confirmar = requests.put(
    f"{BASE_URL}/api/pedidos/{pedido['id']}",
    json={"estado_id": 2, "local_despacho_id": 13},
    headers=headers
).json()

print(f"\n✅ Pedido confirmado")
print(f"   Total real: ${confirmar['total']}")
print(f"   Estado: {confirmar['estado_nombre']}")

# Asignar despacho
despacho_data = {
    "pedido_id": pedido['id'],
    "despachador_user_id": 28  # Admin El Olivo
}

despacho = requests.post(
    f"{BASE_URL}/api/despachos/asignar/{pedido['id']}",
    json=despacho_data,
    headers=headers
).json()

print(f"\n✅ Despacho asignado: ID {despacho['id']}")
print(f"   Estado despacho: {despacho['estado_despacho']}")
print(f"   Picking items: {len(despacho['picking_items'])}")

print(f"\n" + "="*60)
print(f"🎯 PEDIDO DE PRUEBA CREADO")
print(f"   Pedido: {pedido['numero_pedido']}")
print(f"   Despacho ID: {despacho['id']}")
print(f"   URL: http://elolivo.local:3001/admin/despacho/{despacho['id']}")
print(f"\n📋 PRUEBA:")
print(f"   1. Ir a la URL del despacho")
print(f"   2. Cambiar estado a ENTREGADO")
print(f"   3. Verificar que el pedido también pase a ENTREGADO")
print("="*60)
